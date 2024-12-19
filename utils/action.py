def get_client_ip(group, request):
    # Lấy IP từ X-Forwarded-For nếu có, hoặc fallback sang REMOTE_ADDR
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()  # Lấy IP đầu tiên trong danh sách
    return request.META.get('REMOTE_ADDR', '')