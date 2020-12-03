import yfinance as yf
import pandas as pd
import datetime
from matplotlib import pyplot as plt


df_tsla = yf.download(tickers='TSLA', period='1mo', interval='30m')
df_vt = yf.download(tickers='VT', period='1mo', interval='30m')

df_tsla = df_tsla.reset_index()
df_tsla = df_tsla[['Datetime', 'Close']]

df_vt = df_vt.reset_index()
df_vt = df_vt[['Datetime', 'Close']]

# Merge
df = df_tsla.merge(df_vt, how='outer', on='Datetime', suffixes=('_tsla', '_vt'))

# Timezone (convert to European)
df['Datetime'] = df['Datetime'].dt.tz_convert('Europe/Berlin')

# Take just from my trade
trade_date = pd.Timestamp(year=2020, month=11, day=30, hour=18, minute=30, tz='Europe/Berlin')
df = df[df['Datetime'] >= trade_date]

# Price as what I originally paid (and adjust the df to be identical for plotting)
init_val_tsla = -5 * 582.21
init_val_vt = 32 * 88.865

df.iloc[0, 1] = 582.21
df.iloc[0, 2] = 88.865

# Add columns of value of my position at that time
df['TSLA Value'] = -5 * df['Close_tsla']
df['VT Value'] = 32 * df['Close_vt']

# Recall also paying 0.25% in interest per year (maybe a bit more idk)

# Get .diff
df['TSLA P&L'] = df['TSLA Value'] - init_val_tsla
df['VT P&L'] = df['VT Value'] - init_val_vt
df['Total P&L'] = df['TSLA P&L'] + df['VT P&L']

# Save df to csv (merge with old)
df_current = pd.read_csv('data.csv', parse_dates=[0])
df_current['Datetime'] = df_current['Datetime'].dt.tz_convert('Europe/Berlin')  # re-localise pre-concat

df = pd.concat([df_current, df])
df = df.drop_duplicates(subset=['Datetime'], keep='last')

df.to_csv('data.csv', index=False)

# Model our data
fig, ax = plt.subplots(figsize=(14, 7))
ax.plot(df['Datetime'], df['TSLA P&L'], label='TSLA Short')
ax.plot(df['Datetime'], df['VT P&L'], label='VT Long')
ax.plot(df['Datetime'], df['Total P&L'], label='Total')

cur_pnl = df['Total P&L'].iloc[-1]
tsla_pnl = df['TSLA P&L'].iloc[-1]
vt_pnl = df['VT P&L'].iloc[-1]

ax.set_title(f'Relative Trade P&L (-5 TSLA, +32 VT) - $2911 trade: \${tsla_pnl:.0f} TSLA, \${vt_pnl:.0f} VT, \${cur_pnl:.0f} Total')
ax.set_ylabel('P&L (USD)')
ax.set_ylabel('Datetime (30min intervals & trading days)')
ax.legend()

# Max and min highlight
ymax = df['Total P&L'].max()
xmax = df[df['Total P&L']==ymax]['Datetime']
ymin = df['Total P&L'].min()
xmin = df[df['Total P&L']==ymin]['Datetime']

ax.annotate(f'${ymax:.0f}', xy=(xmax, ymax), xytext=(xmax, ymax))
ax.annotate(f'${ymin:.0f}', xy=(xmin, ymin), xytext=(xmin, ymin-10))

plt.savefig('the_great_short.png')

