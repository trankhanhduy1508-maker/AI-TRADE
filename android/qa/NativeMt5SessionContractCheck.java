import vn.cws.aitrade.NativeMt5SessionContract;

public final class NativeMt5SessionContractCheck {
    private static void ok(boolean v){ if(!v) throw new AssertionError(); }
    public static void main(String[] args){
        ok(NativeMt5SessionContract.validServer("Broker-Server-Demo"));
        ok(!NativeMt5SessionContract.validServer(""));
        ok(!NativeMt5SessionContract.validServer("bad\nserver"));
        ok(NativeMt5SessionContract.validLogin("12345678"));
        ok(!NativeMt5SessionContract.validLogin("012345"));
        ok(!NativeMt5SessionContract.validLogin("1234"));
        ok(NativeMt5SessionContract.validPassword("mock-password-only"));
        ok(!NativeMt5SessionContract.validPassword("abc"));
        ok(!NativeMt5SessionContract.validPassword("123456789012345678901234567890123"));
        ok(!NativeMt5SessionContract.validPassword("bad\npassword"));
        ok("••••5678".equals(NativeMt5SessionContract.maskLogin("12345678")));
        ok(NativeMt5SessionContract.connectedStatus("CONNECTED"));
        ok(NativeMt5SessionContract.connectedStatus("CONNECTED_READ_ONLY"));
        ok(!NativeMt5SessionContract.connectedStatus("ERROR"));
        System.out.println("PASS: 14 MT5 session contract checks");
    }
}
