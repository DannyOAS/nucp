# api/utils.py
def create_filter_queryset(base_queryset, request, field_mappings):
    """
    Factory method to filter querysets based on request parameters
    
    Args:
        base_queryset: The base queryset to filter
        request: The request object containing query parameters
        field_mappings: Dictionary mapping query param names to model fields
        
    Returns:
        Filtered queryset
    """
    queryset = base_queryset
    
    for param, field in field_mappings.items():
        value = request.query_params.get(param)
        if value:
            filter_kwargs = {field: value}
            queryset = queryset.filter(**filter_kwargs)
            
    return queryset
