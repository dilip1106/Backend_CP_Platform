from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Submission
from accounts.additional_models import UserActivity, UserAchievement, Achievement


@receiver(post_save, sender=Submission)
def update_user_activity(sender, instance, created, **kwargs):
    """
    Update user activity when a submission is created
    """
    if created:
        today = timezone.now().date()
        activity, created = UserActivity.objects.get_or_create(
            user=instance.user,
            date=today,
            defaults={'submissions_count': 0, 'problems_solved': 0}
        )
        
        # Increment submission count
        activity.submissions_count += 1
        
        # If accepted, increment problems solved
        if instance.is_accepted:
            # Check if this is the first accepted submission for this problem today
            previous_accepted = Submission.objects.filter(
                user=instance.user,
                problem=instance.problem,
                verdict='ACCEPTED',
                submitted_at__date=today,
                submitted_at__lt=instance.submitted_at
            ).exists()
            
            if not previous_accepted:
                activity.problems_solved += 1
        
        activity.save()
        
        # Check for achievements
        check_and_award_achievements(instance.user)


def check_and_award_achievements(user):
    """
    Check if user qualifies for any achievements
    """
    # First solve achievement
    if user.total_solved == 1:
        award_achievement(user, 'FIRST_SOLVE')
    
    # Milestone achievements
    if user.total_solved == 10:
        award_achievement(user, 'SOLVE_10')
    elif user.total_solved == 50:
        award_achievement(user, 'SOLVE_50')
    elif user.total_solved == 100:
        award_achievement(user, 'SOLVE_100')
    
    # Streak achievements
    streak = calculate_solve_streak(user)
    if streak >= 30:
        award_achievement(user, 'SOLVE_STREAK_30')
    elif streak >= 7:
        award_achievement(user, 'SOLVE_STREAK_7')


def award_achievement(user, achievement_type):
    """
    Award an achievement to a user if they don't have it
    """
    try:
        achievement = Achievement.objects.get(achievement_type=achievement_type)
        UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement
        )
    except Achievement.DoesNotExist:
        pass


def calculate_solve_streak(user):
    """
    Calculate current solve streak for a user
    """
    from datetime import timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    streak = 0
    current_date = today
    
    while True:
        activity = UserActivity.objects.filter(
            user=user,
            date=current_date,
            problems_solved__gt=0
        ).first()
        
        if activity:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak