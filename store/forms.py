from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Profile, Shop, Product, Category, Goods


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone = forms.CharField(max_length=15, required=False)
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    country = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    address = forms.CharField(max_length=255, required=False, widget=forms.Textarea(attrs={'rows': 3}))
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=False)
    is_seller = forms.BooleanField(required=False, initial=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'email': self.cleaned_data.get('email'),
                    'phone': self.cleaned_data.get('phone'),
                    'birth_date': self.cleaned_data.get('birth_date'),
                    'country': self.cleaned_data.get('country') or '',
                    'city': self.cleaned_data.get('city'),
                    'address': self.cleaned_data.get('address'),
                    'gender': self.cleaned_data.get('gender') or None,
                    'is_seller': self.cleaned_data.get('is_seller') or False,
                }
            )
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is None:
                raise forms.ValidationError('Invalid username/email or password.')
            elif not user.is_active:
                raise forms.ValidationError('This account is inactive.')

        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'email', 'phone', 'birth_date', 'country', 'city', 'address', 'gender', 'is_seller')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        if user:
            self.instance.user = user

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            if self.cleaned_data.get('email'):
                profile.user.email = self.cleaned_data['email']
        if commit:
            if profile.user:
                profile.user.save()
            profile.save()
        return profile


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'description', 'logo')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'description', 'category', 'image')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class GoodsForm(forms.ModelForm):
    class Meta:
        model = Goods
        fields = ('product', 'purchase_price', 'selling_price', 'stock', 'is_available')


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your shipping address'}),
        label='Shipping Address'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Any special instructions or notes'}),
        required=False,
        label='Order Notes'
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('wallet', 'Pay with Wallet'),
            ('cod', 'Cash on Delivery'),
        ],
        widget=forms.RadioSelect,
        label='Payment Method'
    )


class AddGoodsToShopForm(forms.Form):
    shop = forms.ModelChoiceField(
        queryset=Shop.objects.none(),
        empty_label="Select a shop",
        label='Select Shop'
    )
    
    product_action = forms.ChoiceField(
        choices=[
            ('existing', 'Select Existing Product'),
            ('new', 'Create New Product')
        ],
        widget=forms.RadioSelect,
        initial='existing',
        label='Product Action'
    )
    
    existing_product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        empty_label="Select a product",
        label='Select Product'
    )

    product_name = forms.CharField(
        max_length=150,
        required=False,
        label='Product Name'
    )
    product_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label='Product Description'
    )
    product_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Select a category",
        label='Product Category'
    )
    product_image = forms.ImageField(
        required=False,
        label='Product Image'
    )

    purchase_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='Purchase Price'
    )
    selling_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='Selling Price'
    )
    stock = forms.IntegerField(
        min_value=0,
        initial=0,
        label='Stock Quantity'
    )
    is_available = forms.BooleanField(
        initial=True,
        required=False,
        label='Available for Sale'
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            user_shops = Shop.objects.filter(owner=user)
            self.fields['shop'].queryset = user_shops
            
            existing_goods_products = Goods.objects.filter(shop__in=user_shops).values_list('product_id', flat=True)
            self.fields['existing_product'].queryset = Product.objects.exclude(id__in=existing_goods_products)

    def clean(self):
        cleaned_data = super().clean()
        product_action = cleaned_data.get('product_action')

        if product_action == 'existing':
            if not cleaned_data.get('existing_product'):
                raise forms.ValidationError('Please select an existing product.')
        elif product_action == 'new':
            if not cleaned_data.get('product_name'):
                raise forms.ValidationError('Product name is required for new products.')
            if not cleaned_data.get('product_category'):
                raise forms.ValidationError('Product category is required for new products.')

        return cleaned_data 