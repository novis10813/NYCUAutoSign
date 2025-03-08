import os
import dotenv
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

from calendar_holiday import get_nycu_calendar_holidays, check_weekend
from nycu_sign import handle_singin_singout

# 載入環境變數
dotenv.load_dotenv()

log_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 設定 logging
logging.basicConfig(
    level=log_mapping[os.getenv("LOG_LEVEL", "INFO")],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# 設定記錄目錄和環境變數
RECORD_DIR = Path(os.getenv("RECORD_DIR", "./record"))
RECORD_DIR.mkdir(parents=True, exist_ok=True)

# 從 .env 獲取每月需要的時數和每月開始日期
MONTHLY_REQUIRED_HOURS = int(os.getenv("MONTHLY_REQUIRED_HOURS", 20))  # 預設20小時
MONTHLY_START_DAY = int(os.getenv("MONTHLY_START_DAY", 1))  # 預設每月1號開始

def get_monthly_holidays(year, month):
    """獲取指定月份的假期"""
    return get_nycu_calendar_holidays(year, month)

def is_workday(date_to_check):
    """檢查是否為工作日（排除周末和假期）"""
    if check_weekend(date_to_check):
        logger.info(f"{date_to_check.strftime('%Y-%m-%d')} 是周末，不簽到")
        return False
    
    holidays = get_monthly_holidays(date_to_check.year, date_to_check.month)
    date_str = date_to_check.strftime("%Y-%m-%d")
    if date_str in holidays:
        logger.info(f"{date_str} 是假期，不簽到")
        return False
    
    return True

def record_attendance(action, timestamp):
    """將簽到/簽退記錄寫入檔案"""
    today = timestamp.date()
    month_file = RECORD_DIR / f"{today.year}_{today.month}.txt"
    
    with open(month_file, "a") as f:
        f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {action}\n")
    logger.info(f"記錄 {action} 時間: {timestamp}")

def get_month_start_date(today=None):
    """根據 MONTHLY_START_DAY 計算本月開始日期"""
    if today is None:
        today = datetime.now().date()
    
    year, month = today.year, today.month
    try:
        start_date = datetime(year, month, MONTHLY_START_DAY).date()
    except ValueError:
        # 如果日期無效（例如2月30號），調整到該月最後一天
        next_month = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        start_date = (next_month - timedelta(days=1)).date()
    
    # 如果今天早於本月開始日期，返回下個月開始日期
    if today < start_date:
        return start_date
    return start_date

def get_total_hours(start_date=None):
    """計算從本月開始日期到現在的總工作時數"""
    if start_date is None:
        start_date = get_month_start_date()
    
    today = datetime.now().date()
    month_file = RECORD_DIR / f"{today.year}_{today.month}.txt"
    if not month_file.exists():
        return 0
    
    total_hours = 0
    with open(month_file, "r") as f:
        lines = f.readlines()
        sign_in_time = None
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.strip().split()
            if len(parts) < 3:
                continue
                
            log_date, log_time, action = parts[0], parts[1], parts[2]
            log_datetime = datetime.strptime(f"{log_date} {log_time}", "%Y-%m-%d %H:%M:%S")
            
            # 只計算本月開始日期之後的記錄
            if log_datetime.date() < start_date:
                continue
                
            if action == "SignIn":
                sign_in_time = log_datetime
            elif action == "SignOut" and sign_in_time:
                work_duration = (log_datetime - sign_in_time).total_seconds() / 3600
                total_hours += int(work_duration)
                sign_in_time = None
    
    return total_hours

def get_daily_hours(today=None):
    """計算今天已經記錄的工作時數"""
    if today is None:
        today = datetime.now().date()
    
    month_file = RECORD_DIR / f"{today.year}_{today.month}.txt"
    if not month_file.exists():
        return 0
    
    daily_hours = 0
    today_str = today.strftime("%Y-%m-%d")
    
    with open(month_file, "r") as f:
        lines = f.readlines()
        sign_in_time = None
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.strip().split()
            if len(parts) < 3:
                continue
                
            log_date, log_time, action = parts[0], parts[1], parts[2]
            if log_date != today_str:
                continue
                
            if action == "SignIn":
                sign_in_time = datetime.strptime(f"{log_date} {log_time}", "%Y-%m-%d %H:%M:%S")
            elif action == "SignOut" and sign_in_time:
                sign_out_time = datetime.strptime(f"{log_date} {log_time}", "%Y-%m-%d %H:%M:%S")
                work_duration = (sign_out_time - sign_in_time).total_seconds() / 3600
                daily_hours += int(work_duration)
                sign_in_time = None
    
    return daily_hours

def auto_check_in_out(check_in_hour=9, daily_work_hours=8):
    """自動簽到和簽退，根據每月所需時數控制"""
    while True:
        now = datetime.now()
        today = now.date()
        
        # 檢查是否為工作日
        if not is_workday(today):
            logger.info("今天不是工作日，等待到明天...")
            time.sleep(60 * 60)
            continue
        
        # 計算本月開始日期
        month_start_date = get_month_start_date(today)
        
        # 如果今天早於本月開始日期，等待到開始日期
        if today < month_start_date:
            wait_seconds = (datetime.combine(month_start_date, datetime.min.time()) - now).total_seconds()
            logger.info(f"本月從 {month_start_date} 開始，等待 {int(wait_seconds / 3600)} 小時")
            time.sleep(wait_seconds)
            continue
        
        # 檢查本月是否已完成所需時數
        total_hours = get_total_hours(month_start_date)
        if total_hours >= MONTHLY_REQUIRED_HOURS:
            logger.info(f"本月從 {month_start_date} 開始已完成 {total_hours} 小時，達到或超過 {MONTHLY_REQUIRED_HOURS} 小時，等待下個月")
            next_month_start = (month_start_date.replace(day=MONTHLY_START_DAY) + timedelta(days=32)).replace(day=MONTHLY_START_DAY)
            wait_seconds = (datetime.combine(next_month_start, datetime.min.time()) - now).total_seconds()
            time.sleep(wait_seconds)
            continue
        
        # 檢查今天是否已完成每日工時
        daily_hours = get_daily_hours(today)
        if daily_hours >= daily_work_hours:
            logger.info(f"今天已完成 {daily_hours} 小時工作，等待到明天")
            time.sleep(24 * 60 * 60)
            continue
        
        # 設定簽到時間
        check_in_time = now.replace(hour=check_in_hour, minute=0, second=0, microsecond=0)
        check_out_time = check_in_time + timedelta(hours=daily_work_hours)
        
        # 如果當前時間早於簽到時間，等待到簽到時間
        if now < check_in_time:
            wait_seconds = (check_in_time - now).total_seconds()
            logger.info(f"等待到 {check_in_hour}:00 簽到，還有 {int(wait_seconds/60)} 分鐘")
            time.sleep(wait_seconds)
        
        # 執行簽到
        try:
            handle_singin_singout()  # 簽到
            sign_in_time = datetime.now()
            record_attendance("SignIn", sign_in_time)
        except Exception as e:
            logger.error(f"簽到失敗: {e}")
            time.sleep(60)
            continue
        
        # 等待到簽退時間
        while True:
            now = datetime.now()
            time_left = (check_out_time - now).total_seconds()
            
            if now >= check_out_time:
                try:
                    handle_singin_singout()  # 簽退
                    sign_out_time = datetime.now()
                    record_attendance("SignOut", sign_out_time)
                    logger.info(f"簽退完成，今天工作 {int((sign_out_time - sign_in_time).total_seconds() / 3600)} 小時")
                    time.sleep(24 * 60 * 60)
                    break
                except Exception as e:
                    logger.error(f"簽退失敗: {e}")
                    time.sleep(60)
            else:
                hours_left = time_left / 3600
                logger.info(f"距離簽退還有 {hours_left:.2f} 小時")
                time.sleep(60)

if __name__ == "__main__":
    auto_check_in_out(check_in_hour=9, daily_work_hours=4)