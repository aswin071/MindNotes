"""
URL Configuration for Premium Focus Programs
"""

from django.urls import path
from .premium_views import *

urlpatterns = [
    # Common endpoints
    path('premium/access/', PremiumAccessCheckView.as_view(), name='premium-access-check'),
    path('premium/stats/', PremiumProgramStatsView.as_view(), name='premium-stats'),
    path('premium/brain-dump/categories/', BrainDumpCategoriesView.as_view(), name='brain-dump-categories'),

    # Morning Charge endpoints
    path('premium/morning-charge/start/', MorningChargeStartView.as_view(), name='morning-charge-start'),
    path('premium/morning-charge/breathing/', MorningChargeBreathingView.as_view(), name='morning-charge-breathing'),
    path('premium/morning-charge/gratitude/', MorningChargeGratitudeView.as_view(), name='morning-charge-gratitude'),
    path('premium/morning-charge/affirmation/', MorningChargeAffirmationView.as_view(), name='morning-charge-affirmation'),
    path('premium/morning-charge/clarity/', MorningChargeClarityView.as_view(), name='morning-charge-clarity'),
    path('premium/morning-charge/close/', MorningChargeCloseView.as_view(), name='morning-charge-close'),
    path('premium/morning-charge/complete/', MorningChargeCompleteView.as_view(), name='morning-charge-complete'),
    path('premium/morning-charge/history/', MorningChargeHistoryView.as_view(), name='morning-charge-history'),
    path('premium/morning-charge/today/', MorningChargeTodayView.as_view(), name='morning-charge-today'),

    # Brain Dump Reset endpoints
    path('premium/brain-dump/start/', BrainDumpStartView.as_view(), name='brain-dump-start'),
    path('premium/brain-dump/settle-in/', BrainDumpSettleInView.as_view(), name='brain-dump-settle-in'),
    path('premium/brain-dump/thoughts/', BrainDumpAddThoughtsView.as_view(), name='brain-dump-thoughts'),
    path('premium/brain-dump/guided-responses/', BrainDumpGuidedResponsesView.as_view(), name='brain-dump-guided-responses'),
    path('premium/brain-dump/categorize/', BrainDumpCategorizeView.as_view(), name='brain-dump-categorize'),
    path('premium/brain-dump/choose-task/', BrainDumpChooseTaskView.as_view(), name='brain-dump-choose-task'),
    path('premium/brain-dump/close-breathe/', BrainDumpCloseBreatheView.as_view(), name='brain-dump-close-breathe'),
    path('premium/brain-dump/complete/', BrainDumpCompleteView.as_view(), name='brain-dump-complete'),
    path('premium/brain-dump/history/', BrainDumpHistoryView.as_view(), name='brain-dump-history'),
    path('premium/brain-dump/today/', BrainDumpTodayView.as_view(), name='brain-dump-today'),

    # Gratitude Pause endpoints
    path('premium/gratitude-pause/start/', GratitudePauseStartView.as_view(), name='gratitude-pause-start'),
    path('premium/gratitude-pause/arrive/', GratitudePauseArriveView.as_view(), name='gratitude-pause-arrive'),
    path('premium/gratitude-pause/three-gratitudes/', GratitudePauseThreeGratitudesView.as_view(), name='gratitude-pause-three-gratitudes'),
    path('premium/gratitude-pause/deep-dive/', GratitudePauseDeepDiveView.as_view(), name='gratitude-pause-deep-dive'),
    path('premium/gratitude-pause/expression/', GratitudePauseExpressionView.as_view(), name='gratitude-pause-expression'),
    path('premium/gratitude-pause/anchor/', GratitudePauseAnchorView.as_view(), name='gratitude-pause-anchor'),
    path('premium/gratitude-pause/complete/', GratitudePauseCompleteView.as_view(), name='gratitude-pause-complete'),
    path('premium/gratitude-pause/history/', GratitudePauseHistoryView.as_view(), name='gratitude-pause-history'),
    path('premium/gratitude-pause/today/', GratitudePauseTodayView.as_view(), name='gratitude-pause-today'),
]
