import vn.cws.aitrade.NativeUpdatePolicy;
import java.util.List;
import java.util.Arrays;

public class NativeUpdatePolicyCheck {
    interface Task { void run() throws Exception; }
    private static void bad(Task call) throws Exception {
        try {call.run();}catch(IllegalArgumentException expected){return;}
        throw new AssertionError("Unsafe update accepted");
    }
    private static void ok(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] args) throws Exception {
        String pkg="vn.cws.aitrade";
        String sha="a".repeat(64);
        String url="https://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/v4/cws-autotrade-4.apk";
        NativeUpdatePolicy.requireUpgrade(pkg,3,pkg,4,"stable",100000,sha,url);
        NativeUpdatePolicy.requireUpgrade(pkg,4,pkg,5,"recovery",100000,sha,url);
        bad(()->NativeUpdatePolicy.requireUpgrade(pkg,4,pkg,4,"stable",100000,sha,url));
        bad(()->NativeUpdatePolicy.requireUpgrade(pkg,4,"evil.app",5,"stable",100000,sha,url));
        bad(()->NativeUpdatePolicy.requireUpgrade(pkg,3,pkg,4,"beta",100000,sha,url));
        bad(()->NativeUpdatePolicy.requireUpgrade(pkg,3,pkg,4,"stable",100,sha,url));
        bad(()->NativeUpdatePolicy.releaseUrl("http://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/v4/cws-autotrade-4.apk"));
        bad(()->NativeUpdatePolicy.releaseUrl("https://github.com.evil.test/trankhanhduy1508-maker/AI-TRADE/releases/download/v4/cws-autotrade-4.apk"));
        bad(()->NativeUpdatePolicy.releaseUrl(url+"?redirect=evil"));
        bad(()->NativeUpdatePolicy.releaseUrl(url.replace("v4/", "v4/%2e%2e/")));
        bad(()->NativeUpdatePolicy.releaseUrl(url.replace("cws-autotrade-4.apk","other.apk")));
        byte[] original=new byte[256];Arrays.fill(original,(byte)12);
        byte[] same=original.clone();byte[] wrong=original.clone();wrong[0]^=1;
        ok(NativeUpdatePolicy.sameCertificate(List.of(original),List.of(same)));
        ok(!NativeUpdatePolicy.sameCertificate(List.of(original),List.of(wrong)));
        ok(!NativeUpdatePolicy.sameCertificate(List.of(original),List.of(original,wrong)));
        ok(!NativeUpdatePolicy.sameCertificate(List.of(),List.of(same)));
        System.out.println("PASS: 15 offline APK update policy checks; signer bytes are fake");
    }
}
