package vn.cws.aitrade;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Platform-neutral aggregation of fresh, broker-verified DEMO positions. */
public final class NativePortfolioSummary {
    public static final int MAX_POSITIONS = 1000;

    public static final class Position {
        public final String symbol;
        public final String side;
        public final double lot;
        public final double pnl;

        public Position(String symbol, String side, double lot, double pnl) {
            if (symbol == null || !symbol.matches("[A-Za-z0-9._-]{2,32}")
                || !("BUY".equals(side) || "SELL".equals(side))
                || !Double.isFinite(lot) || lot <= 0 || lot > 1000
                || !Double.isFinite(pnl) || Math.abs(pnl) > 1e9) {
                throw new IllegalArgumentException("INVALID_BROKER_POSITION");
            }
            this.symbol = symbol;
            this.side = side;
            this.lot = lot;
            this.pnl = pnl;
        }
    }

    public static final class Group {
        public final String symbol;
        public final String side;
        public final int count;
        public final double lot;
        public final double pnl;

        private Group(String symbol, String side, int count, double lot, double pnl) {
            this.symbol = symbol;
            this.side = side;
            this.count = count;
            this.lot = lot;
            this.pnl = pnl;
        }
    }

    private static final class Accumulator {
        final String symbol;
        String side;
        int count;
        double lot;
        double pnl;

        Accumulator(String symbol, String side) {
            this.symbol = symbol;
            this.side = side;
        }
        void add(Position p) {
            if (!side.equals(p.side)) side = "HỖN HỢP";
            count++;
            lot += p.lot;
            pnl += p.pnl;
            if (!Double.isFinite(lot) || !Double.isFinite(pnl)) {
                throw new IllegalArgumentException("INVALID_BROKER_TOTAL");
            }
        }
        Group freeze() {
            return new Group(symbol, side, count, lot, pnl);
        }
    }

    public final int positionCount;
    public final int pairCount;
    public final double gain;
    public final double loss;
    public final double net;
    public final List<Group> groups;

    private NativePortfolioSummary(int count, List<Group> groups,
                                   double gain, double loss, double net) {
        this.positionCount = count;
        this.pairCount = groups.size();
        this.groups = Collections.unmodifiableList(groups);
        this.gain = gain;
        this.loss = loss;
        this.net = net;
    }

    public static NativePortfolioSummary of(List<Position> positions) {
        if (positions == null || positions.size() > MAX_POSITIONS) {
            throw new IllegalArgumentException("INVALID_BROKER_POSITION_COUNT");
        }
        Map<String, Accumulator> bySymbol = new LinkedHashMap<>();
        double gain = 0, loss = 0;
        for (Position p : positions) {
            if (p == null) throw new IllegalArgumentException("INVALID_BROKER_POSITION");
            Accumulator group = bySymbol.get(p.symbol);
            if (group == null) {
                group = new Accumulator(p.symbol, p.side);
                bySymbol.put(p.symbol, group);
            }
            group.add(p);
            gain += Math.max(p.pnl, 0);
            loss += Math.min(p.pnl, 0);
            if (!Double.isFinite(gain) || !Double.isFinite(loss)) {
                throw new IllegalArgumentException("INVALID_BROKER_TOTAL");
            }
        }
        List<Group> groups = new ArrayList<>();
        for (Accumulator group : bySymbol.values()) groups.add(group.freeze());
        groups.sort((left, right) -> left.symbol.compareTo(right.symbol));
        return new NativePortfolioSummary(
            positions.size(), groups, gain, loss, gain + loss);
    }

    public String display(String currency) {
        if (currency == null || !currency.matches("[A-Z]{3,8}")) {
            throw new IllegalArgumentException("INVALID_BROKER_CURRENCY");
        }
        StringBuilder out = new StringBuilder();
        out.append("\nTổng lãi: ").append(amount(gain)).append(" ").append(currency);
        out.append("\nTổng lỗ: ").append(amount(loss)).append(" ").append(currency);
        out.append("\nLãi/lỗ ròng: ").append(amount(net)).append(" ").append(currency);
        out.append("\nSố cặp có vị thế: ").append(pairCount);
        for (Group g : groups) {
            out.append("\n").append(g.symbol).append(" | ").append(g.side);
            out.append(" | Số vị thế: ").append(g.count);
            out.append(" | Lot: ").append(String.format(Locale.ROOT, "%.4f", g.lot));
            out.append(" | P/L: ").append(amount(g.pnl)).append(" ").append(currency);
        }
        return out.toString();
    }

    private static String amount(double value) {
        return String.format(Locale.ROOT, "%,.2f", value);
    }
}
