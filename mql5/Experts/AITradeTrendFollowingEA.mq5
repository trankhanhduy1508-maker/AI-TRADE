#property strict
#property version   "1.00"
#property description "AI-TRADE TF-003 deterministic breakout boundary"

#include <Trade/Trade.mqh>

input bool   EnableDemoTrading = false;
input double DemoLots          = 0.01;
input int    BreakoutLookback  = 20;
input int    AtrPeriod         = 14;
input double AtrStopMultiple   = 2.0;
input double RewardMultiple    = 1.5;
input int    MaxSpreadPoints   = 20;
input ulong  MagicNumber       = 15082026;

CTrade   trade;
int      atr_handle            = INVALID_HANDLE;
datetime last_processed_bar    = 0;

bool SafetyGateAllowsTrading()
  {
   if(!EnableDemoTrading)
      return false;
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
      return false;
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      return false;
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      return false;
   if(DemoLots <= 0.0 || DemoLots > 0.01)
      return false;
   if(BreakoutLookback < 2 || AtrPeriod < 1)
      return false;
   return true;
  }

bool SpreadIsAcceptable(const MqlTick &tick)
  {
   if(_Point <= 0.0)
      return false;
   double spread_points = (tick.ask - tick.bid) / _Point;
   return spread_points >= 0.0 && spread_points <= MaxSpreadPoints;
  }

bool HasOurPosition(const string symbol)
  {
   if(!PositionSelect(symbol))
      return false;
   return (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber;
  }

bool ReadAtr(double &atr_value)
  {
   double values[];
   ArraySetAsSeries(values, true);
   if(CopyBuffer(atr_handle, 0, 1, 1, values) != 1)
      return false;
   atr_value = values[0];
   return atr_value > 0.0;
  }

void EvaluateClosedBar()
  {
   int needed = BreakoutLookback + 2;
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_CURRENT, 0, needed, rates) != needed)
      return;

   if(rates[1].time == last_processed_bar)
      return;
   last_processed_bar = rates[1].time;

   if(HasOurPosition(_Symbol))
      return;

   double highest = -1.0e100;
   double lowest  = 1.0e100;
   for(int index = 2; index < needed; index++)
     {
      if(rates[index].high > highest)
         highest = rates[index].high;
      if(rates[index].low < lowest)
         lowest = rates[index].low;
     }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || !SpreadIsAcceptable(tick))
      return;

   double atr_value;
   if(!ReadAtr(atr_value))
      return;

   double stop_distance = atr_value * AtrStopMultiple;
   if(stop_distance <= 0.0)
      return;

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   if(rates[1].close > highest)
     {
      double stop  = NormalizeDouble(tick.ask - stop_distance, digits);
      double target = NormalizeDouble(tick.ask + stop_distance * RewardMultiple, digits);
      if(!SafetyGateAllowsTrading())
         return;
      trade.Buy(DemoLots, _Symbol, 0.0, stop, target, "AI-TRADE TF003 DEMO");
     }
   else if(rates[1].close < lowest)
     {
      double stop  = NormalizeDouble(tick.bid + stop_distance, digits);
      double target = NormalizeDouble(tick.bid - stop_distance * RewardMultiple, digits);
      if(!SafetyGateAllowsTrading())
         return;
      trade.Sell(DemoLots, _Symbol, 0.0, stop, target, "AI-TRADE TF003 DEMO");
     }
  }

int OnInit()
  {
   trade.SetExpertMagicNumber(MagicNumber);
   atr_handle = iATR(_Symbol, PERIOD_CURRENT, AtrPeriod);
   if(atr_handle == INVALID_HANDLE)
      return INIT_FAILED;
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(atr_handle != INVALID_HANDLE)
      IndicatorRelease(atr_handle);
  }

void OnTick()
  {
   if(!SafetyGateAllowsTrading())
      return;
   EvaluateClosedBar();
  }
