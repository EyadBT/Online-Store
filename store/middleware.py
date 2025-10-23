from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
import time
from django.utils import timezone


class AuthenticationMiddleware(MiddlewareMixin):
	
	def process_request(self, request):
		public_urls = [
			'/',
			'/login/',
			'/register/',
			'/admin/',
			'/static/',
			'/media/',
		]
		
		current_path = request.path_info.lstrip('/')
		
		if any(request.path.startswith(url) for url in public_urls):
			return None
		
		if not request.user.is_authenticated:
			messages.warning(request, 'Please log in to access this page.')
			return redirect('store:login')
		
		return None


class SellerMiddleware(MiddlewareMixin):
	
	def process_request(self, request):
		seller_urls = [
			'/shop/create/',
			'/shop/manage/',
			'/product/add/',
			'/goods/add/',
		]
		
		if any(request.path.startswith(url) for url in seller_urls):
			if not request.user.is_authenticated:
				messages.error(request, 'You must be logged in to access this page.')
				return redirect('store:login')
			
			if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
				messages.error(request, 'You must be a seller to access this page.')
				return redirect('store:home')
		
		return None


class UserActivityMiddleware(MiddlewareMixin):
	
	def process_request(self, request):
		if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
			request.user.last_login = timezone.now()
			request.user.save(update_fields=['last_login'])
		
		return None


class RequestLoggingMiddleware(MiddlewareMixin):
	
	def process_request(self, request):
		request.start_time = time.time()
		return None
	
	def process_response(self, request, response):
		if hasattr(request, 'start_time'):
			duration = time.time() - request.start_time
			response['X-Request-Duration'] = str(duration)
		
		return response


class CSRFMiddleware(MiddlewareMixin):
	
	def process_request(self, request):
		if request.method in ['POST', 'PUT', 'DELETE']:
			pass
		return None


class RateLimitMiddleware(MiddlewareMixin):
	
	def __init__(self, get_response):
		super().__init__(get_response)
		self.request_counts = {}
	
	def process_request(self, request):
		client_ip = self.get_client_ip(request)
		
		current_time = time.time()
		minute_ago = current_time - 60
		
		self.request_counts = {
			ip: timestamps for ip, timestamps in self.request_counts.items()
			if any(ts > minute_ago for ts in timestamps)
		}
		
		if client_ip in self.request_counts:
			recent_requests = [ts for ts in self.request_counts[client_ip] if ts > minute_ago]
			if len(recent_requests) > 100:
				return HttpResponseForbidden("Rate limit exceeded. Please try again later.")
			self.request_counts[client_ip].append(current_time)
		else:
			self.request_counts[client_ip] = [current_time]
		
		return None
	
	def get_client_ip(self, request):
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			ip = x_forwarded_for.split(',')[0]
		else:
			ip = request.META.get('REMOTE_ADDR')
		return ip 