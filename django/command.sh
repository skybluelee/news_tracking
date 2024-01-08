sudo apt update
sudo apt install python3-pip
sudo apt install python3-django
django-admin startproject django

vi ~/.bashrc
alias python='python3'
source ~/.bashrc

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py runserver ec2-18-181-191-26.ap-northeast-1.compute.amazonaws.com:8000