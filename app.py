from flask import Flask, render_template, request, redirect, url_for
from khayyam import JalaliDate, JalaliDatetime
from datetime import datetime
import json
import os

app = Flask(__name__)

# File to store tasks
TASKS_FILE = 'tasks.json'

# Load tasks from file (if it exists)
def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tasks', []), data.get('archived_tasks', [])
    return [], []

# Save tasks to file
def save_tasks(tasks, archived_tasks):
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'tasks': tasks, 'archived_tasks': archived_tasks}, f, ensure_ascii=False, indent=2)

# Initialize tasks
tasks, archived_tasks = load_tasks()

@app.route('/', methods=['GET', 'POST'])
def index():
    global tasks, archived_tasks
    if request.method == 'POST':
        task_text = request.form['task']
        gregorian_date_str = request.form.get('date')
        day = request.form.get('day')

        jalali_date_str = None
        if gregorian_date_str:
            gregorian_date = datetime.strptime(gregorian_date_str, '%Y-%m-%d')
            jalali_date = JalaliDate(gregorian_date)
            jalali_date_str = jalali_date.strftime('%Y-%m-%d')

        tasks.append({
            'text': task_text,
            'date': jalali_date_str,
            'day': day,
            'done': False
        })
        save_tasks(tasks, archived_tasks)  # Save after adding
        return redirect(url_for('index'))

    # Auto-archive past-due or done tasks
    current_jalali = JalaliDate.today()
    for i in range(len(tasks) - 1, -1, -1):
        task = tasks[i]
        if task['done'] or (task['date'] and JalaliDate.strptime(task['date'], '%Y-%m-%d') < current_jalali):
            archived_tasks.append(tasks.pop(i))
    save_tasks(tasks, archived_tasks)  # Save after archiving

    current_date = current_jalali
    return render_template('index.html', tasks=tasks, archived_tasks=archived_tasks, current_date=current_date)

@app.route('/toggle/<int:task_id>')
def toggle(task_id):
    global tasks
    if 0 <= task_id < len(tasks):
        tasks[task_id]['done'] = not tasks[task_id]['done']
        save_tasks(tasks, archived_tasks)  # Save after toggling
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    global tasks, archived_tasks
    if 0 <= task_id < len(tasks):
        archived_tasks.append(tasks.pop(task_id))
        save_tasks(tasks, archived_tasks)  # Save after deleting
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit(task_id):
    global tasks
    if 0 <= task_id < len(tasks):
        task = tasks[task_id]
        if request.method == 'POST':
            task['text'] = request.form['task']
            gregorian_date_str = request.form.get('date')
            task['day'] = request.form.get('day')

            if gregorian_date_str:
                gregorian_date = datetime.strptime(gregorian_date_str, '%Y-%m-%d')
                jalali_date = JalaliDate(gregorian_date)
                task['date'] = jalali_date.strftime('%Y-%m-%d')
            else:
                task['date'] = None

            save_tasks(tasks, archived_tasks)  # Save after editing
            return redirect(url_for('index'))
        
        gregorian_date_str = None
        if task['date']:
            jalali_date = JalaliDate.strptime(task['date'], '%Y-%m-%d')
            gregorian_date = jalali_date.todate()
            gregorian_date_str = gregorian_date.strftime('%Y-%m-%d')

        return render_template('edit.html', task=task, task_id=task_id, gregorian_date=gregorian_date_str)
    return redirect(url_for('index'))

@app.route('/archive')
def archive():
    return render_template('archive.html', archived_tasks=archived_tasks)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))