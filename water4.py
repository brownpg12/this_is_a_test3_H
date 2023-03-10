

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random

@st.cache_data
def load_data():
    infile='meter_id_2865_data.csv'
    df1=pd.read_csv(infile)
    df1['consumption']=df1['READ_VALUE'].diff()
    df1['date']=pd.to_datetime(df1['READ_TIME'],format="%d/%m/%Y %H:%M")


    tipsfile='tips_file.csv'
    df_tips=pd.read_csv(tipsfile)
    return df1,df_tips


def get_data(df1):
    if 'exclusion_min_per_hour' not in st.session_state:
        st.session_state.exclusion_min_per_hour=-200.0
    if 'exclusion_max_per_hour' not in st.session_state:
        st.session_state.exclusion_max_per_hour=1000.0
    if 'start_date' not in st.session_state:
        st.session_state.start_date=datetime.date(2022, 1, 1)
        
    min_level=st.session_state.exclusion_min_per_hour
    max_level=st.session_state.exclusion_max_per_hour
    df=df1.loc[(df1.consumption >=min_level) & (df1.consumption < max_level) ].copy()

    
    #01/01/2020 00:00
    df['day']=df['date'].dt.strftime('%Y-%m-%d')
    t=st.session_state.start_date
    test_date=datetime.datetime(t.year, t.month, t.day)

    df=df.loc[df['date']>=test_date]
    
    df_day_sum= df.groupby('day',as_index=False).agg({'consumption': ['sum']})
    df_day_sum.columns = df_day_sum.columns.droplevel(1)
    df_day_sum.reset_index(inplace=True)

    df_day_sum['date']=pd.to_datetime(df_day_sum['day'])
    df_day_sum['month']=df_day_sum['date'].dt.strftime('%Y-%m')
    df_month_avg= df_day_sum.groupby('month').agg({'consumption': ['mean']})
    df_month_avg.columns = ['_'.join(col).strip()  for col in df_month_avg.columns.values]
    df_month_avg.reset_index(inplace=True)
    df_month_avg['date']=pd.to_datetime(df_month_avg['month'],format="%Y-%m")
    df_month_avg['month_name'] = pd.to_datetime(df_month_avg['date']).dt.month_name()    
    df_month_avg['month_with_name'] = df_month_avg['date'].dt.strftime('%Y-%m')+" "+df_month_avg['month_name']
    
    df_day_sum['dayofweek']=df_day_sum['date'].dt.dayofweek
    df_dayofweek_avg= df_day_sum.groupby('dayofweek').agg({'consumption': ['mean']})
    df_dayofweek_avg.columns = ['_'.join(col).strip()  for col in df_dayofweek_avg.columns.values]
    df_dayofweek_avg.reset_index(inplace=True)
    conversion_dict = {0: '0 Monday',1: '1 Tuesday',2:'2 Wednesday',3:'3 Thursday',4:'4 Friday',5:'5 Saturday',6:'6 Sunday'}
    df_dayofweek_avg['day_name'] = df_dayofweek_avg['dayofweek'].map(conversion_dict)
    df_dayofweek_avg.reset_index(inplace=True)
    
    df['time']=df['date'].dt.strftime('%H:%M')
    df_time_avg= df.groupby('time').agg({'consumption': ['mean']})
    df_time_avg.columns = ['_'.join(col).strip()  for col in df_time_avg.columns.values]
    df_time_avg.reset_index(inplace=True)
    
    all_days_stats={}
    all_days_stats['avg']=df_day_sum["consumption"].mean()
    all_days_stats['min']=df_day_sum["consumption"].min()
    all_days_stats['max']=df_day_sum["consumption"].max()

    all_times_stats={}
    all_times_stats['avg']=df["consumption"].mean()
    all_times_stats['min']=df["consumption"].min()
    all_times_stats['max']=df["consumption"].max()

    return df,df_day_sum,df_month_avg,df_dayofweek_avg,df_time_avg,all_days_stats,all_times_stats


def get_stats_for_date(df,this_date):
    print('get_stats_for_date, this_date=',this_date,' type(this_date)=',type(this_date))
    this_day_stats=stats_for_day(df,this_date.strftime('%Y-%m-%d'))
    print('get_stats_for_date, this_day_stats[avg]=',this_day_stats['avg'])
    
    this_dt=pd.to_datetime(this_date)
    previous_day_day=(this_dt - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    previous_day_stats=stats_for_day(df,previous_day_day)

    minus7_day_day=(this_dt - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    minus7_day_stats=stats_for_day(df,minus7_day_day)
    
    this_day_of_the_week=this_dt.weekday()
    df_required_day_of_week=df_day_sum[df_day_sum['dayofweek'] == this_day_of_the_week]
    day_of_week_stats={}
    day_of_week_stats['avg']=df_required_day_of_week["consumption"].mean()
    day_of_week_stats['min']=df_required_day_of_week["consumption"].min()
    day_of_week_stats['max']=df_required_day_of_week["consumption"].max()
    
    return this_day_stats,previous_day_day,previous_day_stats,minus7_day_day,minus7_day_stats,df_required_day_of_week,day_of_week_stats

def stats_for_day(df,date_required):
    this_stats={}
    
    df_required_date=df[df['day'] == date_required]
    if len(df_required_date)>0:
        this_stats['sum']=df_required_date["consumption"].sum()
        this_stats['avg']=df_required_date["consumption"].mean()
        this_stats['min']=df_required_date["consumption"].min()
        this_stats['max']=df_required_date["consumption"].max()
    else:
        this_stats['sum']=float("nan")
        this_stats['avg']=float("nan")
        this_stats['min']=float("nan")
        this_stats['max']=float("nan")

    return this_stats


def markdown_red_green_diff(label,value1,value2):
    if np.isnan(value1) or np.isnan(value2):
        st.markdown(':blue['+f"{label:s}= ---"+']')
    else:
        value=value1-value2
        text_string=f"{label:s}= {value:+.2f}"
        if value==0.0:
            st.markdown(':black['+text_string+']')
        elif value<0.0:
            st.markdown(':green['+text_string+']:heart:')
        else:
            st.markdown(':red['+text_string+']:disappointed:')


def markdown_red_green_diff_pound(label,value1,value2):
    if np.isnan(value1) or np.isnan(value2):
        st.markdown(':blue['+f"{label:s}= ---"+']')
    else:
        value=value1-value2
        text_string1=f"{label:s}="
        text_string2=f"{value:.2f}"
        if value==0.0:
            st.markdown(':black['+text_string1+' No Change '+text_string2+']')
        elif value<0.0:
            st.markdown(':green['+text_string1+' Down '+text_string2+']:heart:')
        else:
            st.markdown(':red['+text_string1+ 'Up '+text_string2+']:disappointed:')


def previous_button_callback():
    this_dt=st.session_state.date_picker
    this_day=this_dt - datetime.timedelta(days=1)
    st.session_state.date_picker=this_day        

def next_button_callback():
    this_dt=st.session_state.date_picker
    this_day=this_dt + datetime.timedelta(days=1)
    st.session_state.date_picker=this_day

def show_a_tip():
    this_tip=df_tips.sample()
    st.info('Here is a tip to cut your water bill:\n'+this_tip.iloc[0,0], icon="ℹ")

pounds_per_litre=0.001776
    
st.set_page_config(page_title='This is a test, this is a test', page_icon='arqiva-favicon_16x16.png', layout="wide")

st.markdown('Do the world a favour, be a water saver')

df1,df_tips=load_data()
df,df_day_sum,df_month_avg,df_dayofweek_avg,df_time_avg,all_days_stats,all_times_stats = get_data(df1)

tab_summary,tab_points,tab_calculator,tab_tip,tab_selected_day,tab_days,tab_months,tab_dayofweek,tab_time,tab_config = st.tabs(['Summary','Points','Calculator','Saving Tip','Selected Day','Days','Months','Week days','hours','config'])

with tab_summary:

    " "
    st.subheader("Last day:")
    min_date=datetime.datetime.strptime(df_day_sum['day'].min(),'%Y-%m-%d')
    max_date=datetime.datetime.strptime(df_day_sum['day'].max(),'%Y-%m-%d')
    st.text('The last day we have data for is: '+max_date.strftime('%d %B %Y'))

    this_day_stats,previous_day_day,previous_day_stats,minus7_day_day,minus7_day_stats,df_required_day_of_week,day_of_week_stats=get_stats_for_date(df_day_sum,max_date)
    st.text(f"  Your consumption through the day is {this_day_stats['sum']:.1f} litres, which is £{this_day_stats['sum']*pounds_per_litre:.2f}" )
    markdown_red_green_diff_pound('  :pound: change from previous day in £ ',this_day_stats['sum']*pounds_per_litre,previous_day_stats['sum']*pounds_per_litre)
    markdown_red_green_diff_pound('  :pound: change from 1 week earlier in £ ',this_day_stats['sum']*pounds_per_litre,minus7_day_stats['sum']*pounds_per_litre)
    markdown_red_green_diff_pound('  :pound: change from average for same day of week in £ ',this_day_stats['sum']*pounds_per_litre,day_of_week_stats['avg']*pounds_per_litre)
        
    " "
    date_difference=max_date - min_date
    num_days=date_difference.days+1
    st.subheader(f"In the last {num_days:d} days:")
    st.text(f"  Your average consumption per day is {all_days_stats['avg']:.1f} litres, which is £{all_days_stats['avg']*pounds_per_litre:.2f} per day" )
    st.text(f"  On the day you used least water, you used {all_days_stats['min']:.1f} litres, which is £{all_days_stats['min']*pounds_per_litre:.2f} per day" )
    st.text(f"  On the day you used most water, you used {all_days_stats['max']:.1f} litres, which is £{all_days_stats['max']*pounds_per_litre:.2f} per day" )

with tab_points:
    df_last7=df[-7:]
    last7_sum=df_last7["consumption"].sum()
    df_previous7=df[-14:-7]
    previous7_sum=df_previous7["consumption"].sum()
    
    points_this_week=int(max(0,last7_sum-previous7_sum))
    points_total_this_year=4356
    if points_this_week>0:
        st.markdown(f"Your used less water in the last 7 days than in the previous 7")
        st.markdown(f"Your water points this week: {points_this_week:d}")
        st.balloons()
    else:
        st.markdown(f"Your used more water in the last 7 days than in the previous 7")
        st.markdown(f"No water points this week")
        
    st.markdown(f"Your total water points this year: {points_total_this_year:d}")
    st.markdown(f":gift: Every point mean you are entered in the prize draw")
with tab_calculator:
    

    col0calc,col1calc, col2calc, col3calc = st.columns(4)
    with col0calc:
        number_of_people=st.slider(':bust_in_silhouette: How many people live in your house?', min_value=0, max_value=10, value=2, step=1,key='slider_people')

        number_of_mixer_showers=st.slider(':shower: How many mixer showers in your house?', min_value=0, max_value=6, value=2, step=1,key='slider_mixer_showers')
        number_of_electric_showers=st.slider(':shower: How many electric showers in your house?', min_value=0, max_value=6, value=2, step=1,key='slider_electric_showers')
        number_of_power_showers=st.slider(':shower: How many power showers in your house?', min_value=0, max_value=6, value=2, step=1,key='slider_power_showers')
        number_showers_per_week_pp=st.slider(':shower: How many shower per week per person?', min_value=0, max_value=14, value=5, step=1,key='slider_showers_per_week')
        washing_machine_capacity=st.radio(':question: Washing machine capacity',    (33.0,50.0,72.0))
        number_of_washes_per_week=st.slider(':question: Number of washing machine loads per week?', min_value=0, max_value=6, value=2, step=1,key='slider_number_washes')
        garden_hose_hours_per_week=st.slider(':sunflower: Hours of garden hose per week?', min_value=0, max_value=6, value=2, step=1,key='slider_garden_hose')

        

        estimate_from_answers=number_of_people*7.0      #7 litres per minute of use, 7 days a week

        estimate_from_answers+=(number_of_people*5*5)       #5 flushes, 5 litres per flush
        
        
        total_showers=number_of_mixer_showers+number_of_electric_showers+number_of_power_showers
        prop_mix=number_of_mixer_showers/total_showers
        prop_electric=number_of_electric_showers/total_showers
        prop_power=number_of_power_showers/total_showers
        average_per_shower=( ( prop_mix*8)+ (prop_electric*5) + (prop_power*13) )
        estimate_from_answers+=(average_per_shower*number_showers_per_week_pp*number_of_people)
        
        estimate_from_answers+=(washing_machine_capacity*number_of_washes_per_week)
        
        estimate_from_answers+=garden_hose_hours_per_week*15.0*60.0

       
    with col1calc:
        
        st.markdown(f"The estimate from your answers is {estimate_from_answers:.1f} litres, which is £{estimate_from_answers*pounds_per_litre:.2f} per day")
        st.metric(':droplet: Your Average consumption per day compared with estimate from your answers', value=round(all_days_stats['avg'],1), delta=round(all_days_stats['avg']-estimate_from_answers,1), delta_color="inverse", help=None, label_visibility="visible")
        difference_answers=all_days_stats['avg']-estimate_from_answers
        if difference_answers>0:
            st.markdown(f"The difference is {round(difference_answers,1):.1f} litres per day")
            st.markdown(f"So you pay £{round(difference_answers*pounds_per_litre*365,0):.0f} more per year")
        else:
            st.markdown(f"The difference is {round(difference_answers,1):.1f} litres per day")
            st.markdown(f"So you pay £{-round(difference_answers*pounds_per_litre*365,0):.0f} less per year")

    with col2calc:
        estimated_consumption=145.0*float(number_of_people)
        if number_of_people>1:
            st.markdown(f"National average consumption per day is {int(round(estimated_consumption,0)):d} litres for {number_of_people:d} people" )
        else:
            st.markdown(f"National average consumption per day is {int(round(estimated_consumption,0)):d} litres for {number_of_people:d} person" )
        st.metric(':droplet: Your Average consumption per day', value=round(all_days_stats['avg'],1), delta=round(all_days_stats['avg']-estimated_consumption,1), delta_color="inverse", help=None, label_visibility="visible")
        difference_national=all_days_stats['avg']-estimated_consumption
        if difference_national>0:
            st.markdown(f"The difference is {round(difference_national,1):.1f} litres per day")
            st.markdown(f"you pay £{round(difference_national*pounds_per_litre*365,0):.0f} more per year")
        else:
            st.markdown(f"The difference is {round(difference_national,1):.1f} litres per day")
            st.markdown(f"you pay £{-round(difference_national*pounds_per_litre*365,0):.0f} less per year")

    with col3calc:
        average_region=400.0
        this_pounds=365.0*all_days_stats['avg']*pounds_per_litre
        st.markdown(f"The average bill in your region is £{int(average_region):d} per year")
        st.metric(':droplet: Your Average bill compared with regional average', value=round(this_pounds,1), delta=round(this_pounds-average_region,1), delta_color="inverse", help=None, label_visibility="visible")
        difference_answers=this_pounds-estimate_from_answers
        if difference_answers>0:
            st.markdown(f"So you pay £{round(difference_answers,0):.0f} more per year")
        else:
            st.markdown(f"So you pay £{-round(difference_answers):.0f} less per year")
        
with tab_tip:
    this_tip=df_tips.sample()
    st.markdown('Here is a tip to cut your water bill:')
    st.markdown(':pound: '+ this_tip.iloc[0,0])
    st.button('Another tip ...')

with tab_selected_day:
    min_date=datetime.datetime.strptime(df_day_sum['day'].min(),'%Y-%m-%d')
    max_date=datetime.datetime.strptime(df_day_sum['day'].max(),'%Y-%m-%d')

    col1b, col2b = st.columns(2)
    with col1b:
        if 'date_picker' not in st.session_state:
            st.session_state.date_picker=datetime.date(2022, 5, 1)
        
        #this_day=st.date_input("Selected date",min_value=min_date,max_value=max_date,key='date_picker',value=datetime.date(2023, 3, 1))
        this_day=st.date_input("Selected date",key='date_picker')
        col_button1,col_button2=st.columns([1, 9],gap='small')
        with col_button1:
            st.button(':arrow_left:',on_click=previous_button_callback)
        with col_button2:
            st.button(':arrow_right:',on_click=next_button_callback)

        this_date2 = datetime.datetime.combine(this_day, datetime.datetime.min.time())
        this_day_stats,previous_day_day,previous_day_stats,minus7_day_day,minus7_day_stats,df_required_day_of_week,day_of_week_stats=get_stats_for_date(df_day_sum,this_date2)

        st.text(this_day.strftime('%d %B %Y %A') )
        st.text(f"total for this day= {this_day_stats['sum']:.1f}" )
        markdown_red_green_diff('change from previous day',this_day_stats['sum'],previous_day_stats['sum'])
        markdown_red_green_diff('change from 1 week earlier',this_day_stats['sum'],minus7_day_stats['sum'])
        markdown_red_green_diff('change from average for same day of week',this_day_stats['sum'],day_of_week_stats['avg'])
    with col2b:
        df_required_date=df[df['day'] == this_day.strftime('%Y-%m-%d')]
        if len(df_required_date)>0:
            st.line_chart(df_required_date,x='time',y='consumption')
        

            
with tab_days:
    'Consumption per day'
    df.set_index(['day'], inplace=True)
    st.bar_chart(df_day_sum,x='day',y='consumption')

with tab_months:
    'Average Consumption per day in each month'
    st.bar_chart(df_month_avg,x='month_with_name',y='consumption_mean')

with tab_dayofweek:
    'Average Consumption per weekday'
    st.bar_chart(df_dayofweek_avg,x='day_name',y='consumption_mean') 

with tab_time:
    'Average Consumption per 1 hour timeslot'
    st.bar_chart(df_time_avg,x='time',y='consumption_mean')

with tab_config:
    st.number_input('Exclude < per hour',key='exclusion_min_per_hour',step=100.0,value=st.session_state.exclusion_min_per_hour)
    st.number_input('Exclude > per hour',key='exclusion_max_per_hour',step=100.0,value=st.session_state.exclusion_max_per_hour)

    t=st.session_state.start_date
    test_date=datetime.datetime(t.year, t.month, t.day)
    st.date_input("Start date",key='start_date',value=test_date)
