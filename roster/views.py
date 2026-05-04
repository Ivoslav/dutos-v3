from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.management import call_command
from io import StringIO
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .models import Announcement, AnnouncementReceipt, DutyShift, DutyType, Soldier, Leave, Announcement, ShiftPreference, AuthorizedDevice, ShiftSwapRequest
from .forms import DutyShiftForm, BatchLeaveForm
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.contrib import messages
from django.db import transaction
import calendar
import datetime
import re












from django.views.decorators.http import require_POST
















# ==========================================
# 🖨️ ЕКСПОРТ НА ГРАФИКА ЗА ПРИНТЕР (PDF)
# ==========================================
from collections import OrderedDict


# ==========================================
# 🌴 ГЕНЕРАТОР НА ОТПУСКИ (УИКЕНД)
# ==========================================


# ==========================================
# 🛂 КПП / ЕЖЕДНЕВНИ ОТПУСКИ
# ==========================================


# ==========================================
# 🖨️ ЕКСПОРТ НА ОТПУСКИ ЗА КПП (PDF)
# ==========================================
