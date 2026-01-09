from django.core.management.base import BaseCommand
from accounts.additional_models import Achievement


class Command(BaseCommand):
    help = 'Create initial achievements'

    def handle(self, *args, **kwargs):
        achievements = [
            {
                'name': 'First Blood',
                'description': 'Solve your first problem',
                'achievement_type': 'FIRST_SOLVE',
                'icon': '🎯'
            },
            {
                'name': 'Problem Solver',
                'description': 'Solve 10 problems',
                'achievement_type': 'SOLVE_10',
                'icon': '⭐'
            },
            {
                'name': 'Expert',
                'description': 'Solve 50 problems',
                'achievement_type': 'SOLVE_50',
                'icon': '🏆'
            },
            {
                'name': 'Master',
                'description': 'Solve 100 problems',
                'achievement_type': 'SOLVE_100',
                'icon': '👑'
            },
            {
                'name': 'Week Warrior',
                'description': 'Maintain a 7-day solving streak',
                'achievement_type': 'SOLVE_STREAK_7',
                'icon': '🔥'
            },
            {
                'name': 'Monthly Champion',
                'description': 'Maintain a 30-day solving streak',
                'achievement_type': 'SOLVE_STREAK_30',
                'icon': '💯'
            },
            {
                'name': 'Easy Peasy',
                'description': 'Solve all easy problems',
                'achievement_type': 'ALL_EASY',
                'icon': '✅'
            },
            {
                'name': 'Competitor',
                'description': 'Participate in your first contest',
                'achievement_type': 'FIRST_CONTEST',
                'icon': '🎪'
            },
        ]
        
        for achievement_data in achievements:
            achievement, created = Achievement.objects.get_or_create(
                achievement_type=achievement_data['achievement_type'],
                defaults=achievement_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created achievement: {achievement.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Achievement already exists: {achievement.name}')
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully created all achievements!'))