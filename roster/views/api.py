from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
import datetime
from datetime import timedelta

from roster.models import (
    Soldier, DutyShift, Leave, AnnouncementReceipt, 
    ShiftPreference, AuthorizedDevice, ShiftSwapRequest
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_my_shifts(request):
    user = request.user 
    soldier = user.soldier
    today = datetime.date.today()
    my_shifts = DutyShift.objects.filter(
        soldier=soldier, 
        date__gte=today
    ).order_by('date')
    data = []
    for shift in my_shifts:
        data.append({
            "date": shift.date.strftime('%Y-%m-%d'),
            "duty_name": shift.duty_type.name,
            "status": shift.status
        })
        
    return Response({
        "status": "success",
        "soldier_name": f"{soldier.rank_title} {soldier.last_name}",
        "faculty_number": soldier.faculty_number,
        "upcoming_shifts": data
    })
   
# --- АПИ 1: Взимане на съобщенията за телефона ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_announcements(request):
    """ Връща разписките за АКТИВНИТЕ съобщения за този курсант """
    soldier = request.user.soldier
    
    # Тъй като бекендът вече автоматично създава разписки за правилните хора,
    # тук просто дърпаме разписките на този войник!
    receipts = AnnouncementReceipt.objects.filter(
        soldier=soldier,
        announcement__is_active=True
    ).select_related('announcement').order_by('-announcement__created_at')
    
    data = []
    for r in receipts:
        data.append({
            "receipt_id": r.id, # Важно за следващата стъпка!
            "title": r.announcement.title,
            "type": r.announcement.announcement_type,
            "type_display": r.announcement.get_announcement_type_display(),
            "message": r.announcement.message,
            "date": r.announcement.created_at.strftime('%d.%m.%Y %H:%M'),
            "is_read": r.is_read
        })
        
    return Response({
        "status": "success",
        "alerts": data
    })

# --- АПИ 2: Цъкане на бутона "РАЗБРАХ" от телефона ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_acknowledge_alert(request):
    soldier = request.user.soldier
    receipt_id = request.data.get('receipt_id')

    if not receipt_id:
        return Response({"detail": "Липсва ID на разписката."}, status=400)

    try:
        receipt = AnnouncementReceipt.objects.get(id=receipt_id, soldier=soldier)
        
        # Ако вече не го е прочел, го маркираме
        if not receipt.is_read:
            receipt.is_read = True
            receipt.read_at = timezone.now() # Записваме точния час и секунда!
            receipt.save()
            
        return Response({"status": "success", "message": "Оповестяването е маркирано като прочетено."})
        
    except AnnouncementReceipt.DoesNotExist:
        return Response({"detail": "Разписката не е намерена или нямаш достъп до нея."}, status=404)


# --- АПИ ЗА ТАБ 3: ЖЕЛАНИЯ / БОРСА ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_submit_preference(request):
    """ Позволява на курсанта да каже кога ИСКА или НЕ МОЖЕ да е наряд """
    soldier = request.user.soldier
    
    date_str = request.data.get('date')
    preference = request.data.get('preference') # Очакваме 'want' или 'cannot'

    if not date_str or preference not in ['want', 'cannot']:
        return Response({"detail": "Невалидни данни. Изпратете 'date' и 'preference'."}, status=400)

    try:
        pref_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({"detail": "Грешен формат на датата. Използвайте YYYY-MM-DD."}, status=400)

    # Не могат да дават желания за минали дати
    if pref_date < datetime.date.today():
        return Response({"detail": "Не можете да заявявате желания за минали дати."}, status=400)

    # Записваме или обновяваме желанието (ако вече е цъкнал веднъж)
    obj, created = ShiftPreference.objects.update_or_create(
        soldier=soldier,
        date=pref_date,
        defaults={'preference': preference}
    )

    action_text = "доброволец" if preference == 'want' else "блокиран"
    return Response({
        "status": "success", 
        "message": f"Денят {date_str} е маркиран като {action_text}."
    })
 
@api_view(['POST'])
@permission_classes([AllowAny]) 
def api_device_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    device_id = request.data.get('device_id') # <--- Хардуерният отпечатък
    device_name = request.data.get('device_name', 'Unknown Device')

    if not username or not password or not device_id:
        return Response({"detail": "Липсват задължителни данни (username, password, device_id)."}, status=400)

    # 1. Проверяваме паролата
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({"detail": "Грешен факултетен номер или парола."}, status=401)
        
    soldier = getattr(user, 'soldier', None)
    if not soldier or not soldier.is_active:
        return Response({"detail": "Акаунтът е неактивен."}, status=403)

    # 2. ПРОВЕРКА НА УСТРОЙСТВОТО (Zero Trust магията)
    # Опитваме се да намерим това устройство в базата
    device, created = AuthorizedDevice.objects.get_or_create(
        device_id=device_id,
        defaults={
            'soldier': soldier,
            'device_name': device_name
        }
    )

    # Ако устройството вече съществува, но е вързано за ДРУГ курсант -> КРАЖБА!
    if device.soldier != soldier:
        return Response({"detail": "ВНИМАНИЕ: Това устройство е регистрирано на друг курсант!"}, status=403)

    # Ако си го блокирал през Админ панела
    if not device.is_active:
        return Response({"detail": "Достъпът от това устройство е забранен от Администратор."}, status=403)

    # Записваме от кое IP влиза (За следене)
    client_ip = request.META.get('REMOTE_ADDR')
    device.last_ip_address = client_ip
    device.save()

    # 3. ВСИЧКО Е ТОЧНО -> ИЗДАВАМЕ СЕРТИФИКАТА (JWT)
    refresh = RefreshToken.for_user(user)

    return Response({
        "status": "success",
        "message": f"Добре дошли, {soldier.last_name}",
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    })
    
# --- АПИ ЗА ТАБ 1/3: ПРОФИЛ И ТОЧКИ ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """ Връща пълното досие на курсанта за екрана 'Моят Профил' """
    soldier = request.user.soldier
    today = datetime.date.today()

    # 1. Взимаме предстоящите отпуски/болнични
    upcoming_leaves = Leave.objects.filter(
        soldier=soldier,
        end_date__gte=today
    ).order_by('start_date')

    leaves_data = []
    for l in upcoming_leaves:
        leaves_data.append({
            "type": l.get_leave_type_display(),
            "start": l.start_date.strftime('%Y-%m-%d'),
            "end": l.end_date.strftime('%Y-%m-%d'),
            "reason": l.reason or ""
        })

    # 2. Взимаме заявените желания (за да може приложението да ги оцвети в календара)
    preferences = ShiftPreference.objects.filter(
        soldier=soldier,
        date__gte=today
    )
    
    # Правим го на речник { "2026-10-25": "want", "2026-10-26": "cannot" } за лесно четене от телефона
    pref_data = { p.date.strftime('%Y-%m-%d'): p.preference for p in preferences }

    # 3. Пакетираме всичко
    return Response({
        "status": "success",
        "profile": {
            "first_name": soldier.first_name,
            "last_name": soldier.last_name,
            "rank_title": soldier.rank_title,
            "position": soldier.get_position_display(),
            "company": soldier.company,
            "platoon": soldier.platoon,
            "score": soldier.score,
        },
        "upcoming_leaves": leaves_data,
        "preferences": pref_data
    })
    


# --- БОРСА 1: Виж какво има на борсата (GET) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_market_list(request):
    """ Връща всички наряди, които в момента търсят заместник """
    # Взимаме само отворените заявки от бъдещи дати
    open_requests = ShiftSwapRequest.objects.filter(
        status='open',
        shift__date__gte=datetime.date.today()
    ).select_related('shift', 'shift__duty_type', 'requester')

    data = []
    for req in open_requests:
        data.append({
            "swap_id": req.id,
            "date": req.shift.date.strftime('%Y-%m-%d'),
            "duty_name": req.shift.duty_type.name,
            "requester_name": f"{req.requester.rank_title} {req.requester.last_name}",
            "reason": req.reason
        })
        
    return Response({"status": "success", "market_items": data})


# --- БОРСА 2: Пусни твоя наряд на борсата (POST) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_market_put(request):
    """ Курсант пуска свой наряд на борсата """
    soldier = request.user.soldier
    shift_id = request.data.get('shift_id')
    reason = request.data.get('reason')

    if not shift_id or not reason:
        return Response({"detail": "Липсват данни (shift_id, reason)."}, status=400)

    try:
        shift = DutyShift.objects.get(id=shift_id, soldier=soldier)
    except DutyShift.DoesNotExist:
        return Response({"detail": "Този наряд не е твой или не съществува."}, status=403)

    if shift.date < datetime.date.today():
        return Response({"detail": "Не можеш да сменяш минали наряди."}, status=400)

    # Създаваме заявката в Борсата
    swap, created = ShiftSwapRequest.objects.get_or_create(
        shift=shift,
        defaults={'requester': soldier, 'reason': reason}
    )

    if not created:
        return Response({"detail": "Този наряд вече е пуснат на борсата!"}, status=400)

    return Response({"status": "success", "message": "Нарядът е пуснат на борсата успешно!"})


# --- БОРСА 3: Вземи чужд наряд от борсата (POST) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_market_take(request):
    """ Друг курсант се съгласява да вземе наряда """
    soldier = request.user.soldier
    swap_id = request.data.get('swap_id')

    swap = get_object_or_404(ShiftSwapRequest, id=swap_id)

    if swap.status != 'open':
        return Response({"detail": "Този наряд вече не е наличен на борсата."}, status=400)
    
    if swap.requester == soldier:
        return Response({"detail": "Не можеш да вземеш собствения си наряд."}, status=400)

    # Проверяваме дали кандидатът нарушава 24-часовата почивка (Вчера, Днес или Утре)
    if DutyShift.objects.filter(
        soldier=soldier, 
        date__in=[
            swap.shift.date, 
            swap.shift.date - datetime.timedelta(days=1), 
            swap.shift.date + datetime.timedelta(days=1)
        ]
    ).exists():
        return Response({"detail": "Нарушаваш 24-часовата почивка! Вече си наряд вчера, днес или утре."}, status=400)

    # Променяме статуса и записваме кандидата
    swap.substitute = soldier
    swap.status = 'waiting' # Чака Капитана!
    swap.save()

    return Response({"status": "success", "message": "Ти предложи да вземеш наряда. Чака се одобрение от Капитан."})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_daily_roster(request):
    date_str = request.GET.get('date')
    
    if date_str:
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"detail": "Грешен формат на датата. Използвайте YYYY-MM-DD."}, status=400)
    else:
        target_date = datetime.date.today()

    shifts = DutyShift.objects.filter(
        date=target_date
    ).exclude(status='admin_draft').select_related('soldier', 'duty_type').order_by('-duty_type__weight')
    
    data = []
    for shift in shifts:
        data.append({
            "duty_name": shift.duty_type.name,
            "soldier_name": f"{shift.soldier.rank_title} {shift.soldier.smart_name}",
            "company": shift.soldier.company,
            "status": shift.status # public_draft или official
        })
        
    return Response({
        "status": "success",
        "date": target_date.strftime('%Y-%m-%d'),
        "shifts": data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_test_cursor(request):
    return Response({
        "status": "success",
        "message": "Cursor работи перфектно!"
    })
