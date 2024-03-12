from datetime import datetime
from jobs.jobs import check_paypal_payments
from apscheduler.schedulers.background import BackgroundScheduler

def start():
    scheduler = BackgroundScheduler()
    
    #trigger every 4 minutes
    scheduler.add_job(check_paypal_payments, 'interval', seconds=300)

    scheduler.start()
