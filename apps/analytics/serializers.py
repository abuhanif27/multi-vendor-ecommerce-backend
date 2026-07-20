from rest_framework import serializers

class WidgetDataSerializer(serializers.Serializer):
    title = serializers.CharField()
    value = serializers.CharField()
    delta_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    delta_label = serializers.CharField(required=False, allow_null=True)
    chart_labels = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    chart_data = serializers.ListField(child=serializers.FloatField(), required=False, allow_null=True)

class SalesSummarySerializer(serializers.Serializer):
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    order_count = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    cancellation_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    return_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

class TopProductSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    units_sold = serializers.IntegerField()
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)

class DashboardOverviewResponseSerializer(serializers.Serializer):
    sales_summary = SalesSummarySerializer()
    widgets = WidgetDataSerializer(many=True)
    top_products = TopProductSerializer(many=True)
