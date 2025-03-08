import re
import requests
import logging

from typing import List
from icalendar import Calendar
from datetime import datetime, date, timedelta

# 設定 logger
logger = logging.getLogger(__name__)

def get_nycu_calendar_holidays(year=None, month=None) -> List[str]:
    """
    使用 iCal 格式獲取陽明交通大學行事曆中的放假日
    
    Args:
        year: 年份，默認為當前年份
        month: 月份，默認為當前月份
        
    Returns:
        dict: 包含放假日期及原因的字典
    """
    # 如果未指定年月，使用當前年月
    if year is None or month is None:
        now = datetime.now()
        year = now.year if year is None else year
        month = now.month if month is None else month
    
    # Google Calendar 的 iCal 格式 URL
    ical_url = "https://calendar.google.com/calendar/ical/aanycu%40gmail.com/public/basic.ics"
    
    try:
        # 獲取 iCal 數據
        response = requests.get(ical_url)
        response.raise_for_status()
        
        # 解析 iCal 數據
        cal = Calendar.from_ical(response.content)
        
        holidays = set()
        
        # 遍歷所有事件
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary', ''))
                
                # 檢查是否包含"(放假)"或"連假"等字眼
                if "(放假)" in summary or "連假" in summary:
                    # 獲取事件日期
                    start_date_obj = component.get('dtstart').dt
                    
                    # 根據不同類型的日期對象進行處理
                    if isinstance(start_date_obj, datetime):
                        # 如果是 datetime 對象，轉換為 date
                        event_date = start_date_obj.date()
                    elif isinstance(start_date_obj, date):
                        # 如果已經是 date 對象，直接使用
                        event_date = start_date_obj
                    else:
                        # 其他類型（如 time）則跳過
                        continue
                    
                    # 檢查是否為連假，並解析日期範圍
                    date_range_match = re.search(r'(\d+)日-(\d+)日', summary)
                    if date_range_match and "連假" in summary:
                        start_day = int(date_range_match.group(1))
                        end_day = int(date_range_match.group(2))
                        
                        # 確保開始日期與事件日期一致
                        if start_day != event_date.day:
                            # 如果不一致，以事件日期為準
                            start_day = event_date.day
                        
                        # 為連假的每一天創建假日記錄
                        for day in range(start_day, end_day + 1):
                            try:
                                holiday_date = date(event_date.year, event_date.month, day)
                                
                                # 檢查是否為指定年月
                                if holiday_date.year == year and holiday_date.month == month:
                                    date_str = f"{holiday_date.year}-{holiday_date.month}-{holiday_date.day}"
                                    holidays.add(date_str)
                            except ValueError:
                                # 處理無效日期（如2月30日）
                                continue
                            
                    else:
                        # 非連假或無法解析日期範圍的情況
                        # 檢查是否為指定年月
                        if event_date.year == year and event_date.month == month:
                            date_str = f"{event_date.year}-{event_date.month}-{event_date.day}"
                            holidays.add(date_str)
                    
                    # 處理跨月連假的情況
                    end_date_obj = component.get('dtend')
                    if end_date_obj is not None:
                        end_date = end_date_obj.dt
                        if isinstance(end_date, datetime):
                            end_date = end_date.date()
                        
                        if isinstance(end_date, date) and end_date > event_date:
                            # 計算連假的總天數
                            delta = (end_date - event_date).days
                            
                            # 為連假的每一天創建假日記錄
                            for i in range(delta):
                                holiday_date = event_date + timedelta(days=i)
                                
                                # 檢查是否為指定年月
                                if holiday_date.year == year and holiday_date.month == month:
                                    date_str = f"{holiday_date.year}-{holiday_date.month}-{holiday_date.day}"
                                    holidays.add(date_str)
        
        return sorted(list(holidays))
    
    except Exception as e:
        logger.error(f"獲取行事曆時發生錯誤: {e}")
        return []
    
def check_weekend(date: datetime) -> bool:
    """
    檢查日期是否為周末
    """
    return date.weekday() >= 5


# 測試函數
if __name__ == "__main__":
    holidays = get_nycu_calendar_holidays()
    print("本月放假日:")
    for date in holidays:
        print(f"{date}")