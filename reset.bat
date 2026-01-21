@echo off
echo ==========================================
echo 🛑 ZAPOCHVA PULEN RESTART NA SISTEMATA...
echo ==========================================

echo.
echo 1. Iztrivane i generirane na armiya (Medical/Navy)...
python manage.py seed_data

echo.
echo 2. Nastroika na pravilata za naryadi...
python manage.py fix_duties

echo.
echo 3. Generirane na grafik za DNES...
python manage.py generate_roster 2026-01-21

echo.
echo ==========================================
echo ✅ GOTOVO! Vsi4ko e svezho i nastroeno.
echo ==========================================
pause