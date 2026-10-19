# frozen_string_literal: true

class VisitingTimeCalculator
  def initialize(visiting, office, adjustment_time = 0, specified_departure_time = nil)
    @visiting = visiting
    @office = office
    @adjustment_time = adjustment_time
    @specified_departure_time = specified_departure_time
  end

  def calculate
    ActiveRecord::Base.transaction do
      customers_and_points = @visiting.customers_and_points

      case customers_and_points.size
      when 0
        handle_empty_visiting
      when 1
        handle_single_customer(customers_and_points.first)
      else
        handle_multiple_customers(customers_and_points)
      end

      update_requested_sources
    end
  end

  private

  def handle_empty_visiting
    @visiting.update!(departure_time: nil, arrival_time: nil)
  end

  def handle_single_customer(visiting_customer)
    SingleCustomerTimeCalculator.new(
      @visiting,
      visiting_customer,
      @office,
      @adjustment_time,
      @specified_departure_time
    ).calculate
  end

  def handle_multiple_customers(customers_and_points)
    MultipleCustomersTimeCalculator.new(
      @visiting,
      customers_and_points,
      @office,
      @adjustment_time,
      @specified_departure_time
    ).calculate
  end

  def update_requested_sources
    @visiting.customers.where(is_requested: true).find_each(&:update_requested_source)
  end
end
