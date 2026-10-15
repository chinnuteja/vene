# frozen_string_literal: true

# rubocop:disable Metrics/ClassLength
class DistanceRouteOptimizer
  def self.haversine_distance(lat1, lon1, lat2, lon2)
    rad_per_deg = Math::PI / 180
    earth_radius_m = 6_371_000

    dlat_rad = (lat2 - lat1) * rad_per_deg
    dlon_rad = (lon2 - lon1) * rad_per_deg

    lat1_rad = lat1 * rad_per_deg
    lat2_rad = lat2 * rad_per_deg

    a = (Math.sin(dlat_rad / 2)**2) +
        (Math.cos(lat1_rad) * Math.cos(lat2_rad) * (Math.sin(dlon_rad / 2)**2))
    c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

    earth_radius_m * c
  end

  # メインエントリーポイント：グループベースのルート最適化
  def self.sort_by_distance(departure_latlng, waypoints, _office_category, visiting = nil)
    return [] if waypoints.empty?

    departure_lat, departure_lng = departure_latlng.split(',').map(&:to_f)

    # 出発地点（事業所）のpoint_idを取得
    departure_point_id = visiting&.departure_bookmark&.bid || visiting&.office&.find_bookmark&.bid

    # 到着地点（事業所）のpoint_idを取得
    arrival_point_id = visiting&.arrival_bookmark&.bid || visiting&.office&.find_bookmark&.bid

    # Step 1: stop_mapを構築
    stop_map = build_stop_map(waypoints, visiting)

    # Step 2: 到着地点を分離
    arrival_stops, non_arrival_stops = partition_arrival_stops(stop_map)

    # Step 3: グループ化（base_point_id + soge_type）
    groups = build_groups(non_arrival_stops, visiting)

    # Step 4: グループをセット化（同じbase_point_idの迎え+送りをまとめる、ただし出発/到着地点は除く）
    group_sets = build_group_sets(groups, departure_point_id, arrival_point_id)

    # Step 5: 各グループ内を先に最適化（出発・到着地点を決定するため）
    groups.each do |group|
      optimize_group_internally(group, departure_lat, departure_lng, visiting)
    end

    # Step 6: グループセットの出発・到着地点を計算
    calculate_set_endpoints(group_sets, departure_lat, departure_lng, visiting)

    # Step 7: グループセット間の順序を決定（グリーディ）
    ordered_sets = order_group_sets_greedy(group_sets, departure_lat, departure_lng, departure_point_id,
                                           arrival_point_id)

    # Step 8: 順序に従ってIDを収集
    ordered_ids = collect_ordered_ids(ordered_sets, stop_map)

    # Step 9: 到着地点を最後に追加
    arrival_ids = arrival_stops.pluck(:id)
    ordered_ids.concat(arrival_ids)

    # 結果をフォーマット
    format_result(ordered_ids, stop_map)
  end

  # stop_mapの構築
  def self.build_stop_map(waypoints, visiting = nil)
    stop_map = {}

    waypoints.each do |wp|
      stop_id = "stop_#{wp[:id]}"
      stop_data = {
        id: stop_id,
        original_id: wp[:id],
        lat: wp[:lat].to_f,
        lon: wp[:lng].to_f,
        soge_type: wp[:soge_type],
        point_type: wp[:point_type],
        arrival: wp[:arrival] || false
      }

      # VisitingsCustomerの場合、base_point_idを取得
      if wp[:point_type] == 'VisitingsCustomer'
        vc = find_visitings_customer(wp, visiting)
        stop_data[:base_point_id] = vc&.base_point_id
      end

      stop_map[stop_id] = stop_data
    end

    stop_map
  end

  # VCオブジェクトを取得
  def self.find_visitings_customer(wp, visiting)
    if wp[:object].present? && wp[:object].is_a?(VisitingsCustomer)
      wp[:object]
    elsif visiting&.customers&.loaded?
      visiting.customers.find { |c| c.id == wp[:id] }
    else
      VisitingsCustomer.find_by(id: wp[:id])
    end
  end

  # 到着地点とそれ以外を分離
  def self.partition_arrival_stops(stop_map)
    stops = stop_map.values
    arrival = stops.select { |s| s[:arrival] == true }
    non_arrival = stops.reject { |s| s[:arrival] == true }
    [arrival, non_arrival]
  end

  # グループ化（base_point_id + soge_type）
  def self.build_groups(stops, visiting)
    groups = {}

    # VCをグループ化
    vc_stops = stops.select { |s| s[:point_type] == 'VisitingsCustomer' }
    vc_stops.each do |stop|
      group_key = "#{stop[:base_point_id]}_#{stop[:soge_type]}"
      groups[group_key] ||= {
        key: group_key,
        base_point_id: stop[:base_point_id],
        soge_type: stop[:soge_type],
        soge_type_symbol: dropoff_stop?(stop) ? :drop_off : :pick_up,
        stops: [],
        vp_stop: nil,
        ordered_vc_ids: [],
        first_vc_location: nil,
        last_vc_location: nil
      }
      groups[group_key][:stops] << stop
    end

    # VPをグループに紐づけ
    vp_stops = stops.select { |s| s[:point_type] == 'VisitingsPoint' }
    vp_stops.each do |vp_stop|
      vp = visiting&.base_points&.find { |bp| bp.id == vp_stop[:original_id] }
      if vp
        group_key = "#{vp.point_id}_#{vp_stop[:soge_type]}"
        if groups[group_key]
          groups[group_key][:vp_stop] = vp_stop
        else
          # 独立したVPグループ
          groups[group_key] = {
            key: group_key,
            base_point_id: vp.point_id,
            soge_type: vp_stop[:soge_type],
            soge_type_symbol: dropoff_stop?(vp_stop) ? :drop_off : :pick_up,
            stops: [vp_stop],
            vp_stop: nil,
            ordered_vc_ids: [],
            first_vc_location: nil,
            last_vc_location: nil
          }
        end
      else
        group_key = "vp_#{vp_stop[:original_id]}_#{vp_stop[:soge_type]}"
        groups[group_key] = {
          key: group_key,
          base_point_id: nil,
          soge_type: vp_stop[:soge_type],
          soge_type_symbol: dropoff_stop?(vp_stop) ? :drop_off : :pick_up,
          stops: [vp_stop],
          vp_stop: nil,
          ordered_vc_ids: [],
          first_vc_location: nil,
          last_vc_location: nil
        }
      end
    end

    groups.values
  end

  # グループをセット化（同じbase_point_idの迎え+送りをまとめる、ただし出発/到着地点は別々に扱う）
  def self.build_group_sets(groups, departure_point_id, arrival_point_id)
    sets = []
    sets_by_base_point = {}

    groups.each do |group|
      base_point_id = group[:base_point_id]

      # 出発地点または到着地点の場合は、送りと迎えを別々のセットにする
      if base_point_id == departure_point_id || base_point_id == arrival_point_id
        set = {
          base_point_id:,
          pick_up_group: group[:soge_type_symbol] == :pick_up ? group : nil,
          drop_off_group: group[:soge_type_symbol] == :drop_off ? group : nil,
          start_lat: nil,
          start_lng: nil,
          end_lat: nil,
          end_lng: nil
        }
        sets << set
      else
        # 中間地点（病院など）は同じbase_point_idでまとめる
        sets_by_base_point[base_point_id] ||= {
          base_point_id:,
          pick_up_group: nil,
          drop_off_group: nil,
          start_lat: nil,
          start_lng: nil,
          end_lat: nil,
          end_lng: nil
        }

        if group[:soge_type_symbol] == :pick_up
          sets_by_base_point[base_point_id][:pick_up_group] = group
        else
          sets_by_base_point[base_point_id][:drop_off_group] = group
        end
      end
    end

    sets.concat(sets_by_base_point.values)
  end

  # グループ内を最適化（VCの順序を決定）- 貪欲法
  # 迎え: baseから最も遠い人を1番目 → その地点から近い順
  # 送り: baseから最も近い人を1番目 → その地点から近い順
  def self.optimize_group_internally(group, departure_lat, departure_lng, visiting)
    vc_stops = group[:stops].select { |s| s[:point_type] == 'VisitingsCustomer' }
    return if vc_stops.empty?

    base_lat, base_lng = determine_base_point(group, departure_lat, departure_lng, visiting)

    ordered_ids = greedy_order_within_group(vc_stops, base_lat, base_lng, group[:soge_type_symbol])

    group[:ordered_vc_ids] = ordered_ids

    # 最初と最後のVCの位置を記録
    return unless ordered_ids.any?

    first_stop = vc_stops.find { |s| s[:id] == ordered_ids.first }
    last_stop = vc_stops.find { |s| s[:id] == ordered_ids.last }
    group[:first_vc_location] = { lat: first_stop[:lat], lng: first_stop[:lon] } if first_stop
    group[:last_vc_location] = { lat: last_stop[:lat], lng: last_stop[:lon] } if last_stop
  end

  # グループ内を貪欲法で並べ替え
  def self.greedy_order_within_group(vc_stops, base_lat, base_lng, soge_type_symbol)
    return [] if vc_stops.empty?

    remaining = vc_stops.dup
    ordered_ids = []

    # 最初の地点を選択
    first_stop = if soge_type_symbol == :drop_off
                   # 送り: baseから最も近い人
                   remaining.min_by { |s| haversine_distance(base_lat, base_lng, s[:lat], s[:lon]) }
                 else
                   # 迎え: baseから最も遠い人
                   remaining.max_by { |s| haversine_distance(base_lat, base_lng, s[:lat], s[:lon]) }
                 end

    ordered_ids << first_stop[:id]
    remaining.delete(first_stop)

    current_lat = first_stop[:lat]
    current_lng = first_stop[:lon]

    # 残りは現在地点から最も近い人を選択（貪欲法）
    while remaining.any?
      nearest_stop = remaining.min_by do |s|
        haversine_distance(current_lat, current_lng, s[:lat], s[:lon])
      end

      ordered_ids << nearest_stop[:id]
      remaining.delete(nearest_stop)

      current_lat = nearest_stop[:lat]
      current_lng = nearest_stop[:lon]
    end

    ordered_ids
  end

  # グループセットの出発・到着地点を計算
  def self.calculate_set_endpoints(group_sets, departure_lat, departure_lng, visiting)
    group_sets.each do |set|
      pick_up = set[:pick_up_group]
      drop_off = set[:drop_off_group]

      # セットの出発地点を決定
      if pick_up && pick_up[:first_vc_location]
        # 迎えがある場合: 迎えの最初の利用者
        set[:start_lat] = pick_up[:first_vc_location][:lat]
        set[:start_lng] = pick_up[:first_vc_location][:lng]
      elsif drop_off
        # 送りのみの場合: VP（base_point）
        vp_lat, vp_lng = get_vp_location(drop_off, departure_lat, departure_lng, visiting)
        set[:start_lat] = vp_lat
        set[:start_lng] = vp_lng
      end

      # セットの到着地点を決定
      if drop_off && drop_off[:last_vc_location]
        # 送りがある場合: 送りの最後の利用者
        set[:end_lat] = drop_off[:last_vc_location][:lat]
        set[:end_lng] = drop_off[:last_vc_location][:lng]
      elsif pick_up
        # 迎えのみの場合: VP（base_point）
        vp_lat, vp_lng = get_vp_location(pick_up, departure_lat, departure_lng, visiting)
        set[:end_lat] = vp_lat
        set[:end_lng] = vp_lng
      end
    end
  end

  # VPの位置を取得
  def self.get_vp_location(group, departure_lat, departure_lng, visiting)
    vp_stop = group[:vp_stop]
    return [vp_stop[:lat], vp_stop[:lon]] if vp_stop

    if group[:base_point_id] && visiting&.base_points&.loaded?
      vp = visiting.base_points.find { |bp| bp.point_id == group[:base_point_id] }
      return [vp.bookmark.lat.to_f, vp.bookmark.lng.to_f] if vp&.bookmark
    end

    [departure_lat, departure_lng]
  end

  # グループセット間の順序を決定（グリーディ）
  def self.order_group_sets_greedy(group_sets, departure_lat, departure_lng, departure_point_id, arrival_point_id)
    return group_sets if group_sets.size <= 1

    # 出発地点（事業所）からの送りセットを見つける（あれば最初に固定）
    first_set = find_departure_drop_off_set(group_sets, departure_point_id)

    # 到着地点（事業所）への迎えセットを見つける（あれば最後に固定）
    last_set = find_arrival_pick_up_set(group_sets, arrival_point_id)

    # 中間のセットを抽出
    middle_sets = group_sets.reject { |s| s == first_set || s == last_set }

    # グリーディで順序決定
    ordered = greedy_order_sets(middle_sets, first_set, departure_lat, departure_lng)

    # 結果を組み立て
    result = []
    result << first_set if first_set
    result.concat(ordered)
    result << last_set if last_set
    result.compact
  end

  # 出発地点（事業所）からの送りセットを見つける
  def self.find_departure_drop_off_set(group_sets, departure_point_id)
    return nil unless departure_point_id

    # base_point_idが出発地点（departure_point_id）と同じで、送りのみのセットを探す
    group_sets.find do |s|
      s[:base_point_id] == departure_point_id && s[:drop_off_group] && s[:pick_up_group].nil?
    end
  end

  # 到着地点（事業所）への迎えセットを見つける
  def self.find_arrival_pick_up_set(group_sets, arrival_point_id)
    return nil unless arrival_point_id

    # base_point_idが事業所（arrival_point_id）と同じで、迎えのみのセットを探す
    group_sets.find do |s|
      s[:base_point_id] == arrival_point_id && s[:pick_up_group] && s[:drop_off_group].nil?
    end
  end

  # セットをグリーディで順序決定
  def self.greedy_order_sets(sets, first_set, departure_lat, departure_lng)
    return [] if sets.empty?

    ordered = []
    remaining = sets.dup

    # 現在地を決定（first_setの到着地点、なければ出発地点）
    current_lat = first_set ? (first_set[:end_lat] || departure_lat) : departure_lat
    current_lng = first_set ? (first_set[:end_lng] || departure_lng) : departure_lng

    while remaining.any?
      # 現在地から最も近い出発地点を持つセットを選ぶ
      nearest_set = remaining.min_by do |s|
        haversine_distance(current_lat, current_lng, s[:start_lat] || 0, s[:start_lng] || 0)
      end

      ordered << nearest_set
      remaining.delete(nearest_set)

      # 現在地を更新（セットの到着地点）
      current_lat = nearest_set[:end_lat] || current_lat
      current_lng = nearest_set[:end_lng] || current_lng
    end

    ordered
  end

  # 順序に従ってIDを収集
  def self.collect_ordered_ids(ordered_sets, stop_map)
    ordered_ids = []

    ordered_sets.each do |set|
      # 迎え → 送りの順で処理
      ordered_ids.concat(collect_group_ids(set[:pick_up_group], stop_map)) if set[:pick_up_group]
      ordered_ids.concat(collect_group_ids(set[:drop_off_group], stop_map)) if set[:drop_off_group]
    end

    ordered_ids
  end

  # グループのIDを収集
  def self.collect_group_ids(group, _stop_map)
    ids = []
    vp_stop = group[:vp_stop]

    if group[:soge_type_symbol] == :drop_off
      # 送り: VP → VC
      ids << vp_stop[:id] if vp_stop
      ids.concat(group[:ordered_vc_ids])
    else
      # 迎え: VC → VP
      ids.concat(group[:ordered_vc_ids])
      ids << vp_stop[:id] if vp_stop
    end

    ids
  end

  # 基準点を決定（VP優先）
  def self.determine_base_point(group, start_lat, start_lng, visiting)
    vp_stop = group[:vp_stop]
    return [vp_stop[:lat], vp_stop[:lon]] if vp_stop

    if group[:base_point_id] && visiting&.base_points&.loaded?
      vp = visiting.base_points.find do |bp|
        bp.point_id == group[:base_point_id] && bp.soge_type == group[:soge_type]
      end
      vp ||= visiting.base_points.find { |bp| bp.point_id == group[:base_point_id] }
      return [vp.bookmark.lat.to_f, vp.bookmark.lng.to_f] if vp&.bookmark
    end

    [start_lat, start_lng]
  end

  # 特定地点からの距離でソート
  def self.sort_by_distance_from_point(stops, lat, lng, direction)
    sorted = stops.sort_by do |stop|
      haversine_distance(lat, lng, stop[:lat], stop[:lon])
    end

    sorted = sorted.reverse if direction == :farthest
    sorted.pluck(:id)
  end

  # 結果をフォーマット
  def self.format_result(ordered_ids, stop_map)
    ordered_ids.map.with_index do |stop_id, index|
      stop = stop_map[stop_id]
      next nil unless stop

      {
        id: stop[:original_id],
        lat: stop[:lat],
        lng: stop[:lon],
        soge_type: stop[:soge_type],
        point_type: stop[:point_type],
        order: index + 1
      }
    end.compact
  end

  # dropoff地点かどうか
  def self.dropoff_stop?(stop)
    st = stop[:soge_type]
    st.to_s == 'drop_off' || st.to_i == 2
  end
end
# rubocop:enable Metrics/ClassLength
