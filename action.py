# vim test.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from lxml import html
import pytz

alert_dates = set()

def get_deepest_element(element):
    """
    获取给定元素的最底层子元素。
    假设每个元素最多只有一个子元素。
    
    :param element: lxml element
    :return: 最底层的子元素
    """
    # 持续遍历直到当前元素没有子元素
    while len(element):
        element = element[0]  # 获取当前元素的第一个（也是唯一的）子元素
    return element

def get_text(element):
    """
    获取给定元素的文本内容。
    如果给定元素没有文本内容，返回空字符串。
    
    :param element: lxml element
    :return: 文本内容
    """
    text = element.xpath('.//text()')
    text = [t.strip() for t in text if t.strip() != '']
    return text[0] if text else ''

def add_alert(input_date, input_time, data):
    # 尝试解析输入的日期和时间，检查其合法性
    try:
        dt = datetime.strptime(f"{input_date} {input_time}", "%Y%m%d %H:%M")
    except ValueError:
        # 如果输入的日期或时间不合法，设置为00:00
        dt = datetime.strptime(input_date, "%Y%m%d")

    # 减去12小时，得到t1
    t1 = dt - timedelta(hours=12)
    # 加上12小时，得到t2
    t2 = dt + timedelta(hours=12)

    # 创建北京时区和目标时区(GMT+2)的对象
    tz_beijing = pytz.timezone('Asia/Shanghai')
    tz_target = pytz.timezone('Etc/GMT-2')

    # 将t1和t2转换为带有时区的时间
    t1_aware = tz_beijing.localize(t1)
    t2_aware = tz_beijing.localize(t2)

    # 将t1和t2转换为GMT+02:00的时间
    t1_target = t1_aware.astimezone(tz_target)
    t2_target = t2_aware.astimezone(tz_target)

    # 获取t1和t2覆盖的日期
    # alert_dates.add(t1_target.strftime("%Y%m%d"))
    # alert_dates.add(t2_target.strftime("%Y%m%d"))
    # dates_covered = set()
    # dates_covered.add(t1_target.strftime("%Y%m%d"))
    # dates_covered.add(t2_target.strftime("%Y%m%d"))

    # 如果t1和t2跨越了多天，添加中间的所有日期
    current_date = t1_target.date()
    end_date = t2_target.date()
    while current_date < end_date:
        alert_dates.add(current_date.strftime("%Y%m%d"))
        current_date += timedelta(days=1)
        # dates_covered.add(current_date.strftime("%Y%m%d"))
    print(input_date, input_time, data)
    


# now
# now = datetime.now()
now = datetime.strptime('20240316', '%Y%m%d')

# 未来3天的日历URL
dates = [now + timedelta(days=i) for i in range(3)]
urls = [f"https://rili.jin10.com/day/{(now + timedelta(days=i)).strftime('%Y-%m-%d')}" for i in range(3)]

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver = webdriver.Chrome(options=options)

for date in dates:
    url = f"https://rili.jin10.com/day/{date.strftime('%Y-%m-%d')}"
    driver.get(url)
    html_string = driver.page_source
    doc = html.fromstring(html_string)

    # 获取经济数据
    tr_elements = doc.xpath('//*[@class="jin-table calendar-data-table"]/div[2]/table/tbody/tr')
    economic_data = []
    for tr in tr_elements:
        td_elements = tr.xpath('./td')
        if len(td_elements) == 1:
            continue

        economic_data.append([])

        # 时间
        time = td_elements[0].xpath('.//span')[0].text
        if time is not None:
            economic_data[-1].append(time.strip())
        else:
            if len(economic_data) > 1:
                economic_data[-1].append(economic_data[-2][0])

        # 数据
        data = td_elements[1].xpath('.//span')[1].text
        if data is not None:
            economic_data[-1].append(data.strip())
        else:
            economic_data[-1].append('')

        # 重要性
        importance = td_elements[2].xpath('.//i[not(starts-with(@style, "color: rgb(221, 221, 221)"))]')
        economic_data[-1].append(len(importance))

        # 前值
        previous = get_text(td_elements[3])
        economic_data[-1].append(previous.strip())

        # 预测值
        forecast = get_text(td_elements[4])
        economic_data[-1].append(forecast.strip())

        # 公布值
        actual = td_elements[5].xpath('.//span')[0].text
        economic_data[-1].append(actual.strip())

        # 影响
        impact = td_elements[6].xpath('./div/div')[0].text
        economic_data[-1].append(impact.strip())

    # 获取经济事件
    economic_events = []
    tr_elements = doc.xpath('//*[@class="jin-table calendar-event-table"]/div[2]/table/tbody/tr')
    for tr in tr_elements:
        td_elements = tr.xpath('./td')
        if len(td_elements) < 4:
            continue

        economic_events.append([])

        # 时间
        time = td_elements[0].xpath('.//span')[0].text
        if time is not None:
            economic_events[-1].append(time.strip())
        else:
            if len(economic_events) > 1:
                economic_events[-1].append(economic_events[-2][0])

        # 国家
        country = get_text(td_elements[1])
        economic_events[-1].append(country.strip())

        # 重要性
        importance = td_elements[2].xpath('.//i[not(starts-with(@style, "color: rgb(221, 221, 221)"))]')
        economic_events[-1].append(len(importance))

        # 事件
        event = get_text(td_elements[3])
        economic_events[-1].append(event.strip())
    
    # 判断是否有美国非农/美联储利率/美国CPI数据
    for data in economic_data:
        if '美国' in data[1] and ('非农' in data[1] or '联储利率' in data[1] or 'CPI' in data[1]):
            add_alert(date.strftime('%Y%m%d'), data[0], data)
    
    # for event in economic_events:
    #     print(event)

    # 判断是否有瑞士、加拿大利率决议/公投/选举事件
    for event in economic_events:
        if '瑞士' in event[3] and '利率决议' in event[3]:
            add_alert(date.strftime('%Y%m%d'), event[0], event)
        if '加拿大' in event[3] and '利率决议' in event[3]:
            add_alert(date.strftime('%Y%m%d'), event[0], event)
        if '公投' in event[3] or '选举' in event[3]:
            add_alert(date.strftime('%Y%m%d'), event[0], event)

with open('alert_dates.txt', 'w') as f:
    f.write('\n'.join(alert_dates))

