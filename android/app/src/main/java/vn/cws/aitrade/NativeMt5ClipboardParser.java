package vn.cws.aitrade;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Parses MT5 account-copy text in memory only. Never persists clipboard data. */
public final class NativeMt5ClipboardParser {
    private static final Pattern LOGIN=Pattern.compile(
        "(?im)\\b(?:Login|Account(?:\\s+Number)?)\\b\\s*[:=]?\\s*([1-9][0-9]{4,14})\\b");
    private static final Pattern PASSWORD=Pattern.compile(
        "(?im)\\b(?:Password|Mật\\s*khẩu)\\b\\s*[:=]?\\s*([^\\s]{4,32})");
    private static final Pattern SERVER=Pattern.compile(
        "(?i)\\b([A-Za-z0-9._ -]{2,64}-(?:Demo|DEMO|demo))\\b");

    private NativeMt5ClipboardParser(){}

    public static final class Result {
        public final String login;
        public final String password;
        public final String server;
        Result(String login,String password,String server){
            this.login=login; this.password=password; this.server=server;
        }
        public boolean valid(){
            if(login.isEmpty()||password.isEmpty()) return false;
            return server.isEmpty()||"MetaQuotes-Demo".equalsIgnoreCase(server);
        }
    }

    public static Result parse(String raw){
        if(raw==null||raw.isEmpty()||raw.length()>8192) return new Result("","","");
        String login=capture(LOGIN,raw);
        String password=capture(PASSWORD,raw);
        String server=capture(SERVER,raw);
        if(login.isEmpty()){
            Matcher fallback=Pattern.compile("(?m)^\\s*([1-9][0-9]{4,14})\\s*$").matcher(raw);
            if(fallback.find()) login=fallback.group(1);
        }
        return new Result(login,password,server);
    }

    private static String capture(Pattern pattern,String raw){
        Matcher matcher=pattern.matcher(raw);
        return matcher.find()?matcher.group(1).trim():"";
    }
}
