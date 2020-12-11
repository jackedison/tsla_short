import yfinance as yf
import pandas as pd
import datetime
from matplotlib import pyplot as plt
import sys


def get_data(tickers):
    dfs = []
    for ticker in tickers:
        df = yf.download(tickers=ticker, period='1mo', interval='30m')
        df = df.reset_index()
        df = df[['Datetime', 'Close']]
        df = df.rename(columns={'Close': f'Close_{ticker}'})

        dfs.append(df)

    main_df = dfs[0].merge(dfs[1], how='outer', on='Datetime')
    for next_df in dfs[2:]:
        main_df = main_df.merge(next_df, how='outer', on='Datetime')
    return main_df

def plot_trade(short_tick, short_pos, short_px, long_tick, long_pos, long_px, trade_date):
    df = get_data([short_tick, long_tick])

    # Timezone (convert to European)
    df['Datetime'] = df['Datetime'].dt.tz_convert('Europe/Berlin')

    # Take just from my trade
    df = df[df['Datetime'] >= trade_date]

    # Price as what I originally paid (and adjust the df to be identical for plotting)
    init_val_short = short_pos * short_px
    init_val_long = long_pos * long_px

    df.iloc[0, 1] = short_px
    df.iloc[0, 2] = long_px

    # Add columns of value of my position at that time
    df[f'{short_tick} Value'] = short_pos * df[f'Close_{short_tick}']
    df[f'{long_tick} Value'] = long_pos * df[f'Close_{long_tick}']

    # Recall also paying 0.25% in interest per year (maybe a bit more idk)

    # Get .diff
    df[f'{short_tick} P&L'] = df[f'{short_tick} Value'] - init_val_short
    df[f'{long_tick} P&L'] = df[f'{long_tick} Value'] - init_val_long
    df['Total P&L'] = df[f'{short_tick} P&L'] + df[f'{long_tick} P&L']

    # Save df to csv (merge with old)
    trade_date_str = trade_date.strftime('%Y-%m-%d')
    file_name = f'{trade_date_str}_{short_tick}_{long_tick}'

    try:
        df_current = pd.read_csv(f'{file_name}.csv', parse_dates=[0])
        df_current['Datetime'] = df_current['Datetime'].dt.tz_convert('Europe/Berlin')  # re-localise pre-concat
        df = pd.concat([df_current, df])
        df = df.drop_duplicates(subset=['Datetime'], keep='last')
    except FileNotFoundError:
        pass

    df.to_csv(f'{file_name}.csv', index=False)

    # Model our data
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(df['Datetime'], df[f'{short_tick} P&L'], label=f'{short_tick} Short')
    ax.plot(df['Datetime'], df[f'{long_tick} P&L'], label=f'{long_tick} Long')
    ax.plot(df['Datetime'], df['Total P&L'], label='Total')

    cur_pnl = df['Total P&L'].iloc[-1]
    tsla_pnl = df[f'{short_tick} P&L'].iloc[-1]
    vt_pnl = df[f'{long_tick} P&L'].iloc[-1]

    ax.set_title(f'Relative Trade P&L ({short_pos} {short_tick}, +{long_pos} {long_tick}) - ${init_val_short:.0f} trade: \${tsla_pnl:.0f} {short_tick}, \${vt_pnl:.0f} {long_tick}, \${cur_pnl:.0f} Total')
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

    plt.savefig(f'{file_name}.png')


if __name__ == '__main__':
    # Trade 1 (note: timestamp put 1h earlier I think?)
    trade_date = pd.Timestamp(year=2020, month=11, day=30, hour=18, minute=30, tz='Europe/Berlin')
    plot_trade(short_tick='TSLA', short_pos=-5, short_px=582.21,
               long_tick='VT', long_pos=32, long_px=88.865,
               trade_date=trade_date)

    # Trade 2
    trade_date = pd.Timestamp(year=2020, month=12, day=10, hour=16, minute=00, tz='Europe/Berlin')
    plot_trade(short_tick='SNOW', short_pos=-10, short_px=387.50,
               long_tick='VT', long_pos=42, long_px=91.11,
               trade_date=trade_date)
