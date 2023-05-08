from math import ceil, floor
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import datetime
import streamlit as st
import collections.abc
from pandas.tseries.offsets import DateOffset
import calmap

uploadFile = '2017-2022(month).csv'

def fileUpload():
    global uploadFile
    uploaded_file = st.file_uploader("Выберите файл в формате CSV с разделителем в виде ;", type=['.csv'],accept_multiple_files=False)
    if uploaded_file is not None:
        st.write("Файл успешно добавлен! 😎")

    return uploaded_file
def analysis(file):
    if file.type =='text/csv':
        df = pd.read_csv(file.name, names=['Date', 'MS'], delimiter=';',encoding='utf-8')
        # Предварительная обработка данных
        df.index = pd.to_datetime(df['Date'])
        for i in range(df.shape[0]):
            df['Date'][i] = datetime.datetime.strptime(df["Date"][i], '%Y-%m')
        # df['Date'] = pd.to_datetime(df['Date'])
        # df = df.set_index('Date')
        # Анализ временных рядов
        df = df.resample('MS').sum()
        return df


@st.cache_resource
def forecast(df):
    # Прогнозирование будущих значений
    model = SARIMAX(df, order=(2, 0, 1), seasonal_order=(2, 1, 2, 12), trend='t')
    results = model.fit()
    forecast = results.predict(start=72, end=83, dynamic=True)
    forecast = pd.to_numeric(round(forecast), downcast='integer')
    forecast = forecast.rename("Volume")
    return forecast

@st.cache_data
def forecastFuel(df, forecast):
    # Вывод результата
    # График прогноза расхода  топлива
    fig = plt.figure(figsize=(12, 6))
    plt.plot(df.index[37::], df[37::], label='Исходные данные', color='b', scalex=120)
    plt.plot(forecast.index, forecast, label='Прогноз', color='C1')
    #plt.plot(forecast.index, forecast, 'ro', color='grey')
    plt.plot(forecast.index, forecast.apply(lambda x: x * 1.15), 'r--', color='black')
    plt.plot(forecast.index, forecast.apply(lambda x: x * 0.85), 'r--', color='black')
    plt.legend(loc='upper left')
    plt.xlabel('Дата')
    plt.ylabel('Количество топлива')
    plt.title('Прогноз расхода топлива на следующий год')
    st.pyplot(fig)
    st.title('**Данные прогноза расхода по месяцам**')
    forecast = pd.to_numeric(round(forecast), downcast='integer')
    forecast = forecast.rename("Volume")
    st.table(forecast)
    return forecast


def forecastDate(forecast):
    st.title('Прогнозирование дат завоза топлива')
    fuel_tank = st.number_input('Введите данные по объему топливных цистерн', step=250, value=5000, format='%i',min_value=2500)
    #st.error('This is an error', icon="🚨")
    st.write("Выбранное значение", fuel_tank)
    forecast = pd.to_numeric(round(forecast), downcast='integer')
    # pred_date = [datetime.date(2023, 1, 1) + DateOffset(day=x) for x in range(0, 12)]
    # st.write(pred_date)
    # pred_date = pd.DataFrame(index=pred_date[1:], columns=['Volume'])
    # st.write(pred_date)
    date = []
    data = []
    for index, value in forecast.items():
        pred = value / fuel_tank
        if pred <= 1:
            data.append(value)
            date.append(index + DateOffset(day=0))
        elif pred >= 1:
            pred_date = [index + DateOffset(day=x) for x in range(0, 31, floor(30 / int(pred)))]
            if len(pred_date) != ceil(pred):
                del pred_date[-(len(pred_date)-ceil(pred)):]
            for i in range(int(pred)):
                data.append(fuel_tank)
                value -= fuel_tank
            data.append(value)
            date.append(pred_date)
        else:
            st.write("Ошибка")


    res = []
    for elem in date:
        if  not isinstance(elem, collections.abc.Iterable):
            res.append(elem)
            continue
        for i in range(len(elem)):
            res.append(elem[i])



    prognoz = pd.Series(index=res, data=data, name='Volume')
    pr = pd.DataFrame(data=data, columns=['Volume'])
    pr["Date"] = res

    st.title("**Спрогнозированные значения завоза топлива по дате**")
    view_df = st.checkbox("Отобразить прогнозируемые значения")
    if view_df:

        filter_box = st.checkbox('Добавить фильтры')
        if filter_box:
            st.write('Выберите временные промежутки для отбора')
            start_slider = st.slider(
                "Начало",
                value=datetime.datetime(2023, 1, 1),
                min_value=datetime.datetime(2023, 1, 1),
                max_value=datetime.datetime(2024, 1,1),
                step=pd.Timedelta("1 days"),
                format="MM/DD/YY    ")
            end_slider = st.slider(
                "Конец",
                value=datetime.datetime(2023, 7, 5),
                min_value=datetime.datetime(2023, 1, 1),
                max_value=datetime.datetime(2024, 1, 1),
                step=pd.Timedelta("1 days"),
                format="MM/DD/YY")
            dataSlider = pr[(pr["Date"] >= start_slider) & (pr["Date"] <= end_slider)]
            st.table(dataSlider[['Date','Volume']])
        else:
         # if st.button('Test'):
            st.table(pr[['Date', 'Volume']])

    chart = st.checkbox("Отобразить графики")
    if chart:
        fig = plt.figure(figsize=(12, 6))
        plt.plot(forecast.index, forecast, label='Прогноз', color='C0')
       # plt.plot(prognoz.index, prognoz,'ro--', color='grey')
       #  plt.hist(prognoz, color='blue', edgecolor='black',)
        plt.plot(forecast.index, forecast.apply(lambda x: x * 1.1), 'r--',label="Верхний доверительный интервал", color='C1')
        plt.plot(forecast.index, forecast.apply(lambda x: x * 0.9), 'r--',label="Нижний доверительный интервал", color='C2')
        plt.plot(forecast.index, forecast, 'ro', color='C0')
        plt.legend(loc='upper left')
        plt.xlabel('Дата')
        plt.ylabel('Количество топлива')
        plt.title('Прогноз расхода топлива на следующий год')
        st.pyplot(fig)
        st.title("**Даты завоза топлива в календарном виде**")
        plt.figure(figsize=(12, 5), dpi=120)
        calmap.calendarplot(prognoz, fig_kws={'figsize': (8, 8)},
                            yearlabel_kws={'color': 'black', 'fontsize': 14},
                            subplot_kws={'title': 'Прогноз дат завоза'})

        plt.savefig('foo.png', bbox_inches='tight')
        st.image('foo.png')

def main():
    global uploadFile
    page = st.sidebar.selectbox(
        "Выберите страницу",
        [
            "Загрузка данных",
            "Прогнозирвание расхода топлива",
            "Прогнозирвоание даты завоза топлива",
        ]
    )
    # First Page
    if page == "Загрузка файла":
        pass
        # uploadFile = fileUpload()
        # if uploadFile is not None:
        #     st.write(uploadFile)
    # Second Page
    elif page == "Прогнозирвание расхода топлива":
        forecastFuel(analysis(uploadFile), forecast(analysis(uploadFile)))
    # Third Page
    elif page == "Прогнозирвоание даты завоза топлива":
        forecastDate(forecast(analysis(uploadFile)))
    # Four Page


uploadFile = fileUpload()
if __name__ == '__main__':

    main()

