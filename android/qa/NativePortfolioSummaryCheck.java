import vn.cws.aitrade.NativePortfolioSummary;
import java.util.ArrayList;
import java.util.List;

public final class NativePortfolioSummaryCheck {
    interface Task { void run(); }
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    static void invalid(Task task) {
        try { task.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("Unsafe position summary accepted");
    }
    static NativePortfolioSummary.Position pos(
        String symbol, String side, double lot, double pnl) {
        return new NativePortfolioSummary.Position(symbol, side, lot, pnl);
    }
    public static void main(String[] args) {
        NativePortfolioSummary empty = NativePortfolioSummary.of(List.of());
        check(empty.positionCount == 0 && empty.pairCount == 0);
        check(empty.gain == 0 && empty.loss == 0 && empty.net == 0);
        check(empty.display("USD").contains("Số cặp có vị thế: 0"));

        NativePortfolioSummary sum = NativePortfolioSummary.of(List.of(
            pos("EURUSD", "BUY", .10, 15),
            pos("EURUSD", "SELL", .20, -9),
            pos("XAUUSD", "BUY", .01, -4),
            pos("EURUSD", "BUY", .05, 6)));
        check(sum.positionCount == 4 && sum.pairCount == 2);
        check(sum.gain == 21 && sum.loss == -13 && sum.net == 8);
        check(sum.groups.get(0).symbol.equals("EURUSD"));
        check(sum.groups.get(0).side.equals("HỖN HỢP"));
        check(sum.groups.get(0).count == 3);
        check(Math.abs(sum.groups.get(0).lot - .35) < 1e-12);
        check(sum.groups.get(0).pnl == 12);
        check(sum.groups.get(1).symbol.equals("XAUUSD"));
        check(sum.groups.get(1).side.equals("BUY"));
        check(!sum.display("USD").contains("Tổng Lot"));
        invalid(() -> sum.display("US\\nD"));
        invalid(() -> pos("EURUSD", "BUY", Double.NaN, 3));
        invalid(() -> pos("EURUSD", "BUY", 0, 3));
        invalid(() -> pos("EURUSD", "BUY", .1, Double.POSITIVE_INFINITY));
        invalid(() -> pos("EURUSD", "HOLD", .1, 3));
        invalid(() -> pos("EURUSD<script>", "BUY", .1, 3));
        invalid(() -> NativePortfolioSummary.of(null));
        ArrayList<NativePortfolioSummary.Position> large = new ArrayList<>();
        for (int i = 0; i < 1001; i++) large.add(pos("EURUSD", "BUY", .01, 0));
        invalid(() -> NativePortfolioSummary.of(large));
        System.out.println("PASS: offline DEMO portfolio totals, pair grouping, zero positions and invalid input; broker/device NOT tested");
    }
}
