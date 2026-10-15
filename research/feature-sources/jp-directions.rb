# frozen_string_literal: true

require 'net/http'
require 'uri'
require 'json'

class DirectionsOptimizer
  GOOGLE_DIRECTIONS_API = 'https://maps.googleapis.com/maps/api/directions/json'

  def initialize(origin:, destination:, waypoints:)
    @origin = origin
    @destination = destination
    @waypoints = waypoints
  end

  def optimized_route
    waypoint_param = "optimize:true|#{@waypoints.map { |w| "#{w[:lat]},#{w[:lng]}" }.join('|')}"

    uri = URI(GOOGLE_DIRECTIONS_API)
    uri.query = URI.encode_www_form({
                                      origin: @origin,
                                      destination: @destination,
                                      waypoints: waypoint_param,
                                      mode: 'driving',
                                      key: ENV.fetch('GOOGLE_MAP_API_KEY', nil)
                                    })

    response = Net::HTTP.get(uri)
    json = JSON.parse(response)

    waypoint_order = json.dig('routes', 0, 'waypoint_order') || []
    Rails.logger.debug waypoint_order

    # 最適順に並べ替えて返す（元の地点データと順序付き）
    waypoint_order.map { |i| @waypoints[i].merge(order: i + 1) }
  end
end
