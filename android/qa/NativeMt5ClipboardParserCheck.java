import vn.cws.aitrade.NativeMt5ClipboardParser;

public final class NativeMt5ClipboardParserCheck {
    private static void ok(boolean value){ if(!value) throw new AssertionError(); }
    public static void main(String[] args){
        String copied="Server: MetaQuotes-Demo\nLogin: 1234567890\nPassword: _aB0xYz1\nInvestor: read-only";
        NativeMt5ClipboardParser.Result a=NativeMt5ClipboardParser.parse(copied);
        ok(a.valid());
        ok("1234567890".equals(a.login));
        ok("_aB0xYz1".equals(a.password));
        ok("MetaQuotes-Demo".equalsIgnoreCase(a.server));
        ok(NativeMt5ClipboardParser.parse("Login: 1234567890\nPassword: abcD1234").valid());
        ok(!NativeMt5ClipboardParser.parse("Investor: abcdef").valid());
        ok(!NativeMt5ClipboardParser.parse("Server: Other-Demo\nLogin: 1234567890\nPassword: abcD1234").valid());
        System.out.println("PASS: 7 MT5 clipboard parser checks");
    }
}
