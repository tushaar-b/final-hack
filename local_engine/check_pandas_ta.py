import pandas as pd
import pandas_ta as ta
import numpy as np

df = pd.DataFrame({
    'open': np.random.rand(100),
    'high': np.random.rand(100),
    'low': np.random.rand(100),
    'close': np.random.rand(100),
    'volume': np.random.rand(100)
})
df.ta.atr(length=14, append=True)
df.ta.bbands(length=20, append=True)
print([c for c in df.columns if 'ATR' in c.upper() or 'BB' in c.upper()])
