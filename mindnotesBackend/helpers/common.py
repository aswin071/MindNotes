from django.http import JsonResponse
from rest_framework import status



def success_response(data=None, success_message='Success', status=status.HTTP_200_OK, **kwargs):
    response_data = {'status': True, 'message': success_message, 'results': {},'additional_info':kwargs}
    if data is not None:
        response_data['results']['data'] = data
    return JsonResponse(response_data, status=status)

def error_response(errors={}, error_message='error', status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception_info = None, **kwargs):
    response_data = {'status': False, 'message': error_message, 'errors': errors, "exception_info": exception_info, 'additional_info':kwargs}
    return JsonResponse(response_data, status=status)


def paginated_response(data=None, items=None, success_message='success', status=status.HTTP_200_OK):
    
    response_data = {'status': True, 'message': success_message, 'results': {}}

    if items is not None:
        # Loop through the items and add them to the results dictionary
        for key, value in items.items():
            response_data['results'][key] = value

    # Check if data is present and add it to the results dictionary
    if data is not None:
        response_data['results']['data'] = data

    return JsonResponse(response_data, status=status)