import os
import time
import logging

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from exceptions import (
    LoginException, CredentialsError, LoginFailedError,
    HRSystemError, TimeClockSystemError,
    NavigationException, FrameNavigationError, ElementNotFoundError,
    AttendanceException, SignInError, SignOutError, ConfirmationError
)

# 設定 logger
logger = logging.getLogger(__name__)

def login_to_nycu_portal():
    # 載入環境變數
    load_dotenv()
    
    # 從環境變數獲取帳號密碼
    username = os.getenv("NYCU_USERNAME")
    password = os.getenv("NYCU_PASSWORD")
    
    if not username or not password:
        raise CredentialsError("請在 .env 檔案中設定 NYCU_USERNAME 和 NYCU_PASSWORD")
    
    service = Service(executable_path=ChromeDriverManager().install())
    
    # 設定 Chrome 選項
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    # 初始化 WebDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 直接訪問登入頁面
        driver.get("https://portal.nycu.edu.tw/#/login?redirect=%2F")
        logger.debug("正在訪問陽明交通大學入口網站登入頁面...")
        
        # 等待帳號輸入框出現
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "account"))
        )
        
        # 輸入帳號密碼
        username_input.send_keys(username)
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys(password)
        logger.debug("輸入帳號密碼...")
        
        # 點擊登入按鈕
        login_button = driver.find_element(By.CSS_SELECTOR, "input.login[type='submit']")
        login_button.click()
        logger.debug("點擊登入按鈕...")
        
        # 等待登入成功 (可能需要調整成功判斷條件)
        WebDriverWait(driver, 10).until(
            EC.url_changes("https://portal.nycu.edu.tw/#/login?redirect=%2F")
        )
        logger.info("登入成功！")
        
    except Exception as e:
        logger.error(f"登入過程中發生錯誤: {e}")
        raise LoginFailedError(f"登入過程中發生錯誤: {e}")
    
    try:
        driver.get("https://portal.nycu.edu.tw/#/links/nycu")
        logger.debug("點擊陽明交通大學校園連結...")
        
        # 等待頁面加載完成
        time.sleep(1)
        logger.debug("陽明交通大學校園連結已點擊")
        
        return driver
        
    except Exception as e:
        logger.error(f"點擊陽明交通大學校園連結時發生錯誤: {e}")
        raise LoginException(f"點擊陽明交通大學校園連結時發生錯誤: {e}")

def open_time_clock_system(driver: webdriver.Chrome) -> webdriver.Chrome:
    try:
        logger.debug("尋找人事拆勤系統連結...")
        
        selectors = [
            "a[href='#/redirect/timeClock']",
            "a[title*='人事差勤系統']",
            "a[title*='工時核定']"
        ]
        
        time_clock_link = None
        for selector in selectors:
            try:
                time_clock_link = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.debug(f"找到連結: {time_clock_link.get_attribute('href')}")
                break
            except:
                continue
        
        if time_clock_link is None:
            try:
                time_clock_link = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '人事差勤系統') or contains(@title, '人事差勤系統')]"))
                )
            except:
                # 輸出頁面源碼以便調試
                logger.error("無法找到人事差勤系統連結，頁面源碼:")
                logger.debug(driver.page_source[:1000] + "...")  # 只打印前1000個字符
                raise ElementNotFoundError("無法找到人事差勤系統連結")                
        
        # 紀錄原本的視窗
        original_window = driver.current_window_handle
        
        # 紀錄點擊連結前的視窗數量
        windows_before = driver.window_handles
        
        # 點擊連結
        time_clock_link.click()
        logger.debug("點擊人事拆勤系統")
        
        WebDriverWait(driver, 10).until(
            lambda d: len(d.window_handles) > len(windows_before)
        )
        
        # 切換到新開啟的視窗
        new_window = [window for window in driver.window_handles if window != original_window][0]
        driver.switch_to.window(new_window)
        
        time.sleep(1)
        
        logger.debug(f"已切換到新視窗: {driver.current_url}")
        return driver
    
    except ElementNotFoundError as e:
        raise e
    except Exception as e:
        logger.error(f"開啟人事拆勤系統時發生錯誤: {e}")
        raise TimeClockSystemError(f"開啟人事拆勤系統時發生錯誤: {e}")

def navigate_to_work_hours_system(driver: webdriver.Chrome) -> webdriver.Chrome:
    try:
        logger.debug("等待頁面完全加載...")
        time.sleep(1)  # 增加等待時間確保頁面完全加載
        
        # 檢查是否有框架，如果有則先切換
        frames = driver.find_elements(By.TAG_NAME, "frame")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        
        # 檢查是否有框架需要切換
        if frames or iframes:
            logger.debug(f"找到 {len(frames)} 個框架和 {len(iframes)} 個iframe")
            all_frames = frames + iframes
            
            for i, frame in enumerate(all_frames):
                try:
                    logger.debug(f"嘗試切換到框架 {i}...")
                    driver.switch_to.frame(frame)
                    
                    # 在框架中尋找菜單元素
                    menu_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '我的文件夾')]")
                    if menu_elements:
                        logger.debug(f"在框架 {i} 中找到菜單元素")
                        break
                    driver.switch_to.default_content()
                except:
                    logger.debug(f"切換到框架 {i} 失敗")
                    driver.switch_to.default_content()
        
        # 嘗試使用多種不同的選擇器找到「我的文件夾」
        folder_selector = "//span[@class='ThemeOfficeMainFolderText' and contains(text(), '我的文件夾')]"
        
        # 找到元素
        folder_element = None
        try:
            logger.debug(f"使用選擇器: {folder_selector}")
            elements = driver.find_elements(By.XPATH, folder_selector)
            if elements:
                folder_element = elements[0]
                logger.debug(f"找到元素: {folder_element.text}")
        except Exception as e:
            logger.debug(f"選擇器 {folder_selector} 失敗: {e}")
        
        if not folder_element:
            logger.error("無法找到「我的文件夾」元素")
            logger.debug("頁面源碼片段:")
            logger.debug(driver.page_source[:1000])
            raise ElementNotFoundError("無法找到「我的文件夾」元素")
        
        # 使用ActionChains懸停在元素上並強制顯示子菜單
        logger.debug("嘗試懸停在「我的文件夾」上...")
        actions = ActionChains(driver)
        actions.move_to_element(folder_element).perform()
        
        submenu_id = "cmSubMenuID1"
        driver.execute_script(f"""
            var submenu = document.getElementById('{submenu_id}');
            if (submenu) {{
                submenu.style.visibility = 'visible';
                submenu.style.display = 'block';
                submenu.style.zIndex = '10000';
            }}
        """)
        time.sleep(1)
        
        # 檢查子菜單是否可見
        submenu_elements = driver.find_elements(By.ID, submenu_id)
        if submenu_elements and submenu_elements[0].is_displayed():
            logger.debug(f"子菜單 {submenu_id} 已可見")
        else:
            logger.warning(f"子菜單 {submenu_id} 不可見，檢查 CSS 或 JavaScript 邏輯")
            logger.debug("子菜單 HTML 內容:")
            if submenu_elements:
                logger.debug(driver.execute_script("return arguments[0].outerHTML;", submenu_elements[0]))
            else:
                logger.error("未找到子菜單元素")
                raise ElementNotFoundError("未找到子菜單元素")
                
        if submenu_elements:
            logger.debug("子菜單內容:")
            logger.debug(driver.execute_script("return arguments[0].outerHTML;", submenu_elements[0]))
        
        # 定義目標 XPath
        target_xpath = "//table[@id='cmSubMenuID1Table']//td[normalize-space(text())='受僱者線上簽到退']"

        # 嘗試直接點擊
        try:
            target_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, target_xpath))
            )
            logger.debug(f"找到「受僱者線上簽到退」元素: {target_element.text}")
            target_element.click()
            logger.debug("成功點擊！")
            time.sleep(1)
            return driver
        except Exception as e:
            logger.error(f"直接點擊失敗: {e}")
            raise ElementNotFoundError(f"無法點擊「受僱者線上簽到退」元素: {e}")

    except ElementNotFoundError as e:
        raise e
    except Exception as e:
        logger.error(f"導航過程中發生錯誤: {e}")
        raise NavigationException(f"導航過程中發生錯誤: {e}")
    
def confirmation_button(driver: webdriver.Chrome) -> bool:
    try:
        # 檢查是否有新的 iframe（如果「確定」按鈕在新的 iframe 中）
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            logger.debug(f"找到 {len(iframes)} 個 iframe")
            driver.switch_to.frame(iframes[0])  # 假設仍在第一個 iframe 中

        # 等待並點擊「確定」按鈕
        confirm_xpath = "//input[@id='ContentPlaceHolder1_Button_attend' and @value='確定']"
        confirm_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, confirm_xpath))
        )
        logger.debug("成功找到「確定」按鈕！")
        logger.debug("按鈕 HTML 內容:")
        logger.debug(driver.execute_script("return arguments[0].outerHTML;", confirm_element))

        confirm_element.click()
        logger.debug("已點擊「確定」按鈕！")
        return True
    
    except Exception as e:
        logger.error(f"確定按鈕點擊失敗: {e}")
        raise ConfirmationError(f"確定按鈕點擊失敗: {e}")
        
    
def signin_signout(driver: webdriver.Chrome) -> webdriver.Chrome:
    try:
        logger.debug("開始檢查頁面是否有「簽到SignIn」按鈕...")

        # 定義目標選擇器，根據輸出優化為具體的元素
        target_xpath = "//a[contains(text(), '簽到SignIn') and contains(@class, 'input-button')]"

        # 檢查是否有 iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            logger.debug(f"找到 {len(iframes)} 個 iframe")
            driver.switch_to.frame(iframes[0])  # 切換到第一個 iframe（根據輸出只有 1 個）

        # 等待並查找「簽到SignIn」按鈕
        signin_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, target_xpath))
        )
        logger.debug("成功找到「簽到SignIn」按鈕！")
        logger.debug("按鈕 HTML 內容:")
        logger.debug(driver.execute_script("return arguments[0].outerHTML;", signin_element))

        # 點擊按鈕
        signin_element.click()
        logger.debug("已點擊「簽到SignIn」按鈕！")
        time.sleep(1)  # 等待頁面響應
        
        confirmation_button(driver)
        return driver

    except ConfirmationError as e:
        raise e
    except Exception as e:
        logger.error(f"簽到過程中發生錯誤: {e}")
        raise SignInError(f"簽到過程中發生錯誤: {e}")
    finally:
        # 還原到主內容
        driver.switch_to.default_content()

def signout_button(driver: webdriver.Chrome) -> webdriver.Chrome:
    """
    學校系統超白癡，沒有簽退按鈕，只有簽到按鈕
    """
    try:
        logger.debug("開始檢查頁面是否有「簽退SignOut」按鈕...")

        # 定義目標選擇器，根據輸出優化為具體的元素
        target_xpath = "//a[contains(text(), '簽退SignOut') and contains(@class, 'input-button')]"

        # 檢查是否有 iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            logger.debug(f"找到 {len(iframes)} 個 iframe")
            driver.switch_to.frame(iframes[0])

        # 等待並查找「簽到SignIn」按鈕
        signin_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, target_xpath))
        )
        logger.debug("成功找到「簽退SignOut」按鈕！")
        logger.debug("按鈕 HTML 內容:")
        logger.debug(driver.execute_script("return arguments[0].outerHTML;", signin_element))

        # 點擊按鈕
        signin_element.click()
        logger.debug("已點擊「簽退SignOut」按鈕！")
        time.sleep(1)  # 等待頁面響應

        confirmation_button(driver)
        return driver

    except ConfirmationError as e:
        raise e
    except Exception as e:
        logger.error(f"簽退過程中發生錯誤: {e}")
        raise SignOutError(f"簽退過程中發生錯誤: {e}")
    finally:
        # 還原到主內容
        driver.switch_to.default_content()

def handle_singin_singout():
    try:
        # 第一次操作：簽到
        driver = login_to_nycu_portal()
        logger.info("成功登入陽明交通大學入口網站")

        driver = open_time_clock_system(driver)
        logger.info("成功開啟人事拆勤系統")

        driver = navigate_to_work_hours_system(driver)
        logger.info("成功導航到受雇者線上簽到退頁面")

        # driver = signin_signout(driver)
        # logger.info("簽到操作成功完成！")

    except CredentialsError as e:
        logger.error(f"憑證錯誤: {e}")
        exit(1)
    except LoginFailedError as e:
        logger.error(f"登入失敗: {e}")
        exit(1)
    except LoginException as e:
        logger.error(f"登入過程錯誤: {e}")
        exit(1)
    except TimeClockSystemError as e:
        logger.error(f"人事差勤系統錯誤: {e}")
        exit(1)
    except ElementNotFoundError as e:
        logger.error(f"找不到元素: {e}")
        exit(1)
    except NavigationException as e:
        logger.error(f"導航錯誤: {e}")
        exit(1)
    except SignInError as e:
        logger.error(f"簽到錯誤: {e}")
        exit(1)
    except SignOutError as e:
        logger.error(f"簽退錯誤: {e}")
        exit(1)
    except ConfirmationError as e:
        logger.error(f"確認操作錯誤: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"未預期的錯誤: {e}")
        exit(1)
    finally:
        if 'driver' in locals():
            driver.quit()
            
if __name__ == "__main__":
    # 設定 logging 基本配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handle_singin_singout()