from rest_framework import serializers
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from .models import Contest, ContestRegistration, ContestAnnouncement

User = get_user_model()


class ContestListSerializer(serializers.ModelSerializer):
    """
    Serializer for contest listing (brief view)
    """
    status = serializers.ReadOnlyField()
    manager_username = serializers.CharField(source='manager.username', read_only=True)
    is_registered = serializers.SerializerMethodField()
    
    class Meta:
        model = Contest
        fields = [
            'id', 'title', 'slug', 'description',
            'start_time', 'end_time', 'duration', 'status',
            'manager_username', 'total_participants',
            'is_registered', 'created_at'
        ]
    
    def get_is_registered(self, obj):
        """Check if current user is registered"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ContestRegistration.objects.filter(
                user=request.user,
                contest=obj
            ).exists()
        return False


class ContestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for contest detail view
    """
    status = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_running = serializers.ReadOnlyField()
    is_ended = serializers.ReadOnlyField()
    can_register = serializers.ReadOnlyField()
    
    manager_username = serializers.CharField(source='manager.username', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    is_registered = serializers.SerializerMethodField()
    time_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Contest
        fields = [
            'id', 'title', 'slug', 'description',
            'start_time', 'end_time', 'duration',
            'status', 'is_upcoming', 'is_running', 'is_ended',
            'can_register', 'time_info',
            'manager_username', 'created_by_username',
            'is_public', 'is_active', 'max_participants',
            'total_participants', 'rules', 'scoring_type',
            'is_registered', 'created_at', 'updated_at'
        ]
    
    def get_is_registered(self, obj):
        """Check if current user is registered"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ContestRegistration.objects.filter(
                user=request.user,
                contest=obj
            ).exists()
        return False
    
    def get_time_info(self, obj):
        """Get time-related information"""
        info = {}
        if obj.is_upcoming:
            time_until = obj.time_until_start
            if time_until:
                info['time_until_start'] = str(time_until)
                info['time_until_start_seconds'] = int(time_until.total_seconds())
        elif obj.is_running:
            time_left = obj.time_remaining
            if time_left:
                info['time_remaining'] = str(time_left)
                info['time_remaining_seconds'] = int(time_left.total_seconds())
        return info


class ContestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating contests (SuperUser only)
    """
    manager_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Contest
        fields = [
            'title', 'description', 'start_time', 'end_time',
            'duration', 'manager_id', 'is_public', 'max_participants',
            'rules', 'scoring_type'
        ]
    
    def validate_manager_id(self, value):
        """Validate manager exists and has MANAGER role"""
        if value:
            try:
                user = User.objects.get(id=value)
                if user.role != 'MANAGER':
                    raise serializers.ValidationError(
                        "Selected user is not a Manager. Promote them to Manager first."
                    )
            except User.DoesNotExist:
                raise serializers.ValidationError("Manager not found")
        return value
    
    def validate(self, attrs):
        """Validate start and end times"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        
        return attrs
    
    def create(self, validated_data):
        manager_id = validated_data.pop('manager_id', None)
        
        # Generate slug from title
        validated_data['slug'] = slugify(validated_data['title'])
        
        # Create contest
        contest = Contest.objects.create(**validated_data)
        
        # Assign manager if provided
        if manager_id:
            contest.manager = User.objects.get(id=manager_id)
            contest.save()
        
        return contest


class ContestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating contests (SuperUser only)
    """
    manager_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Contest
        fields = [
            'title', 'description', 'start_time', 'end_time',
            'duration', 'manager_id', 'is_public', 'is_active',
            'max_participants', 'rules', 'scoring_type'
        ]
    
    def validate_manager_id(self, value):
        """Validate manager exists and has MANAGER role"""
        if value:
            try:
                user = User.objects.get(id=value)
                if user.role != 'MANAGER':
                    raise serializers.ValidationError("Selected user is not a Manager")
            except User.DoesNotExist:
                raise serializers.ValidationError("Manager not found")
        return value
    
    def update(self, instance, validated_data):
        manager_id = validated_data.pop('manager_id', None)
        
        # Update slug if title changes
        if 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update manager
        if manager_id is not None:
            if manager_id:
                instance.manager = User.objects.get(id=manager_id)
            else:
                instance.manager = None
        
        instance.save()
        return instance


class ContestRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for contest registrations
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    contest_title = serializers.CharField(source='contest.title', read_only=True)
    
    class Meta:
        model = ContestRegistration
        fields = ['id', 'user_username', 'contest_title', 'registered_at']


class ContestAnnouncementSerializer(serializers.ModelSerializer):
    """
    Serializer for contest announcements
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ContestAnnouncement
        fields = ['id', 'title', 'content', 'created_by_username', 'created_at']


class ContestAnnouncementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating announcements
    """
    class Meta:
        model = ContestAnnouncement
        fields = ['title', 'content']


class ManagerListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing managers (for assignment dropdown)
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)