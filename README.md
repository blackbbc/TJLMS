# Tongji Learning Management System

## Prerequisites
- Python 3.6+
- MongoDB 3.4+

## Install requirements
- [sudo] pip install -r requirements.txt

## Run
Make sure launch `MongoDB`

Run commands

```bash
cd src
python3 -m app
```

Add admin account

```bash
cd src
python -m test.add_admin
```

Now login with `admin:admin`

Add student account

```bash
cd src
python -m test.add_student
```
