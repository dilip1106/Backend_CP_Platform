from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 
                  'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer to include user role and additional info
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        token['role'] = user.role
        token['is_superuser_role'] = user.is_superuser_role
        token['is_manager_role'] = user.is_manager_role
        token['is_normal_user_role'] = user.is_normal_user_role
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'role': self.user.role,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (read operations)
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'full_name', 'role', 'bio', 'avatar', 'country',
                  'total_solved', 'easy_solved', 'medium_solved', 'hard_solved',
                  'date_joined', 'last_login', 'is_active']
        read_only_fields = ['id', 'date_joined', 'last_login', 'total_solved',
                           'easy_solved', 'medium_solved', 'hard_solved']


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for user profile
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'full_name', 'role', 'bio', 'avatar', 'country',
                  'total_solved', 'easy_solved', 'medium_solved', 'hard_solved',
                  'date_joined', 'last_login', 'is_active', 'is_banned']
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login',
                           'total_solved', 'easy_solved', 'medium_solved', 
                           'hard_solved', 'is_banned']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'avatar', 'country']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for user listing (admin view)
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'role', 
                  'total_solved', 'date_joined', 'is_active', 'is_banned']


class RoleChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user roles (SuperUser only)
    """
    role = serializers.ChoiceField(choices=User.Role.choices)
    
    def validate_role(self, value):
        if value == User.Role.SUPER_USER:
            raise serializers.ValidationError(
                "Cannot assign SUPER_USER role through this endpoint."
            )
        return value


class BanActionSerializer(serializers.Serializer):
    """
    Serializer for ban/unban action response
    """
    message = serializers.CharField(read_only=True)
    user = UserListSerializer(read_only=True)