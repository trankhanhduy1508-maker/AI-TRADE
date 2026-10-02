package vn.cws.aitrade;

public final class NativeMt5SessionContract {
    private NativeMt5SessionContract() { }

    public static boolean validServer(String value) {
        if (value == null) return false;
        String s = value.trim();
        if (s.length() < 1 || s.length() > 128) return false;
        for (int i=0;i<s.length();i++) {
            char c=s.charAt(i);
            if (c < 32 || c == 127) return false;
        }
        return true;
    }

    public static boolean validLogin(String value) {
        return value != null && value.matches("[1-9][0-9]{4,14}");
    }

    public static boolean validPassword(String value) {
        // Must match ai-trade-mt5-session and ai-trade-mt5-demo-validate.
        if (value == null || value.length() < 4 || value.length() > 32) return false;
        for (int i=0;i<value.length();i++) {
            char c=value.charAt(i);
            if (c < 32 || c == 127) return false;
        }
        return true;
    }

    public static String maskLogin(String value) {
        if (!validLogin(value)) return "••••";
        int visible=Math.min(4,value.length());
        return "••••"+value.substring(value.length()-visible);
    }

    public static boolean connectedStatus(String status) {
        return "CONNECTED".equals(status) || "CONNECTED_READ_ONLY".equals(status);
    }
}
