# 🧠 Bounty Track

**Bounty Track** is a modern web application designed to manage and track bounties efficiently. It supports secure authentication, powerful data handling features, and insightful visualizations to help users monitor progress and performance over time.

---

## ✨ Features

### 🔐 User Authentication
- Secure login and authorization (Used Django Built in authentication)

### 📥📤 Import / Export
- Import data from CSV files to populate or update report/bounty records

### 📊 Data Visualization with Chart.js
- Interactive charts and graphs for visualizing bounty trends
- Bar charts, or pie charts depending on the data type
- Dynamic updates based on filters or user input

### 📁 Bounty Management
- Create, update, and delete bounties
- Track bounty status and rewards

### 🗂️ Filter, Search & Pagination
- Advanced filtering by date, status, program, platform
- Paginated views for large datasets

### 🧮 Dashboard & Analytics
- Summary cards with total bounties, completed, pending, etc.
- Graphical overview of recent activity and trends

---

## 🛠️ Tech Stack

- **Backend:** Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL / MySQL / SQLite
- **Libraries:** Chart.js, pandas (for import/export), etc.

---

## 🚀 Getting Started

### Manual Installaion
```bash
git clone https://github.com/0xh7ml/BountyTrack.git
cd BountyTrack

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Collect Static Files
python manage.py collectstatic --no-input

python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser # Create User with password

python manage.py runserver
```

### Docker support

Move the `.env.example` to `.env` and update the username and password and if you wanted it mark `DEBUG` true change that too.

```bash
git clone https://github.com/0xh7ml/BountyTrack.git
cd BountyTrack

chmod +x run.sh
./run.sh start

# Visit: http://<ip>:8000
```
> [!IMPORTANT]  
> Make sure you have [docker-compose](https://docs.docker.com/compose/install/) installed in your system

> [!NOTE]  
> You can check logs by entering this command `./run.sh logs` if you see any error you can create a issue.

## 📹 Demo
![Login](http://itsaikat.com/wp-content/uploads/2025/04/Screenshot-2025-04-10-at-12-41-17-Bounty-Track-Login.png)

![Dashboard](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-38.png)

![Reports](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-38_1.png)

![Program Wise Analytics](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-39.png)

![Programs List](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-39_1.png)

![Platform List](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-39_2.png)

![Add Report](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-40.png)

![Import Report](http://itsaikat.com/wp-content/uploads/2025/04/2025-04-10_12-40_1.png)