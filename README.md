# Project Overview
這個專案是用在處理[陽明交通大學](https://portal.nycu.edu.tw/)的工作時數登入系統上，用來自動化每天的工作時數登記。

# 核心功能
- 自動登入工時系統並簽到簽退
- 輸入需要的工時，以及已經登記的工時
- 假日不能登記時數
  - 陽明交通大學的[行事曆](https://www.nycu.edu.tw/nycu/ch/app/artwebsite/view?module=artwebsite&id=476&serno=49696c0f-84e8-4b92-8d34-a43a32e8d642)中，有註明 `(放假)`或`連假` 的日子
  - 颱風假
- 透過 Docker 將功能打包，並且把帳號、密碼、每月需要的工時放在 .env 檔案裡面處理
- 把 SignIn 和 SignOut 紀錄於 .txt 檔，用來確認現在的工時

# How to use

## 透過 Docker

1. 在根目錄設定你的 .env 檔案
```bash
touch .env
```

2. 在 `.env` 檔案裡面填上你的
- 帳號密碼
- 每個月需要的工時
- 每個月幾號開始計算
- 你想把紀錄的檔案存在的地方

```
NYCU_USERNAME=YOUR_ACCOUNT_NAME
NYCU_PASSWORD=YOUR_ACCOUNT_PASSWORD

MONTHLY_REQUIRED_HOURS=REQUIRED_HOURS
MONTHLY_START_DAY=START_DAY
RECORD_DIR=YOUR_SYSTEM_PATH_FOR_RECORD_FILE
```

3. 在根目錄執行以下指令
```bash
docker compose up -d
```

## 直接在系統執行 (recommend)
1. 安裝 poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

如果是 Windows
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

2. 確保你有一個 python=3.13 的環境 (可以用 conda 或其他你喜歡的東西管理)
```bash
conda create -n 3.13 python=3.13
conda activate 3.13
```

3. 在根目錄執行安裝套件
```bash
poetry init
```

4. 在根目錄設定你的 .env 檔案
```bash
touch .env
```

5. 在 `.env` 檔案裡面填上你的
- 帳號密碼
- 每個月需要的工時
- 每個月幾號開始計算
- 你想把紀錄的檔案存在的地方

```
NYCU_USERNAME=YOUR_ACCOUNT_NAME
NYCU_PASSWORD=YOUR_ACCOUNT_PASSWORD

MONTHLY_REQUIRED_HOURS=REQUIRED_HOURS
MONTHLY_START_DAY=START_DAY
RECORD_DIR=YOUR_SYSTEM_PATH_FOR_RECORD_FILE
```

6. 可以執行一次 `src/autoauth/nycu_sign.py` 來簽到，四個小時後會自動簽退
```bash
poetry run python src/autoauth/nycu_sign.py
```

# RoadMap
- Docker
  - 確保能夠長時間正常運作
  - 一天登記八小時，因為目前沒辦法中間休息半小時

- 接 telegram 或其他通訊軟體的 api 查看時數
