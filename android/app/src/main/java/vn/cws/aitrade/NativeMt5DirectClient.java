package vn.cws.aitrade;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

import okio.ByteString;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

public final class NativeMt5DirectClient implements AutoCloseable {
    private static final String WS_URI="wss://web.metatrader.app/terminal";
    private static final byte[] INITIAL_KEY=hex(
        "02de02a1a65cc794684fcbea1ecb0fd74ae657e43662c11eee885d2fd64f4964");
    private final SecureRandom random=new SecureRandom();
    private final LinkedBlockingQueue<byte[]> frames=new LinkedBlockingQueue<>();
    private final OkHttpClient http=new OkHttpClient.Builder()
        .readTimeout(0,TimeUnit.MILLISECONDS).build();
    private volatile Throwable failure;
    private volatile boolean opened;
    private WebSocket socket;
    private byte[] key=INITIAL_KEY.clone();

    public static final class Result {
        public final boolean ok;
        public final int loginCode;
        public final String server;
        public final String currency;
        public final double balance;
        public final boolean tradeAllowed;
        public final boolean readOnly;
        Result(boolean ok,int loginCode,String server,String currency,double balance,
               boolean tradeAllowed,boolean readOnly){
            this.ok=ok; this.loginCode=loginCode; this.server=server;
            this.currency=currency; this.balance=balance;
            this.tradeAllowed=tradeAllowed; this.readOnly=readOnly;
        }
    }

    public Result verify(long login,String password) throws Exception {
        if(login<10000L||password==null||password.length()<4||password.length()>32)
            throw new IllegalArgumentException("INVALID_DIRECT_INPUT");
        Request request=new Request.Builder().url(WS_URI)
            .header("Origin","https://web.metatrader.app").build();
        socket=http.newWebSocket(request,new WebSocketListener(){
            @Override public void onOpen(WebSocket ws,Response response){opened=true;}
            @Override public void onMessage(WebSocket ws,ByteString bytes){
                frames.offer(bytes.toByteArray());
            }
            @Override public void onFailure(WebSocket ws,Throwable t,Response response){
                failure=t;
            }
        });
        long openDeadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(15);
        while(!opened&&failure==null&&System.nanoTime()<openDeadline) Thread.sleep(20);
        if(!opened) throw new java.io.IOException("MT5_DIRECT_WS_OPEN_FAILED");

        Frame boot=command(0,new byte[64],15);
        if(boot.code!=0||boot.body.length<82)
            throw new java.io.IOException("MT5_DIRECT_BOOTSTRAP_FAILED");
        key=Arrays.copyOfRange(boot.body,66,boot.body.length);
        if(!(key.length==16||key.length==24||key.length==32))
            throw new java.io.IOException("MT5_DIRECT_SESSION_KEY");

        byte[] cid=clientId();
        Frame loginFrame=command(28,loginPayload(login,password,cid),20);
        if(loginFrame.code!=0)
            return new Result(false,loginFrame.code,"","",0,false,false);

        Frame account=command(3,new byte[0],15);
        if(account.code!=0) throw new java.io.IOException("MT5_DIRECT_ACCOUNT_READ_FAILED");
        return parseAccount(account.body,loginFrame.code);
    }

    private Frame command(int cmd,byte[] payload,int timeoutSeconds) throws Exception {
        if(failure!=null) throw new java.io.IOException("MT5_DIRECT_WS_FAILED");
        byte[] encrypted=crypt(key,inner(cmd,payload),Cipher.ENCRYPT_MODE);
        if(!socket.send(ByteString.of(outer(encrypted))))
            throw new java.io.IOException("MT5_DIRECT_SEND_FAILED");
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(timeoutSeconds);
        while(System.nanoTime()<deadline){
            if(failure!=null) throw new java.io.IOException("MT5_DIRECT_WS_FAILED");
            byte[] raw=frames.poll(250,TimeUnit.MILLISECONDS);
            if(raw==null) continue;
            if(raw.length<8) continue;
            ByteBuffer head=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
            int len=head.getInt();
            int version=head.getInt();
            if(version!=1||len!=raw.length-8) continue;
            byte[] dec=crypt(key,Arrays.copyOfRange(raw,8,raw.length),Cipher.DECRYPT_MODE);
            if(dec.length<5) continue;
            int id=(dec[2]&255)|((dec[3]&255)<<8);
            if(id!=cmd) continue;
            int code=dec[4]&255;
            return new Frame(code,Arrays.copyOfRange(dec,5,dec.length));
        }
        throw new java.net.SocketTimeoutException("MT5_DIRECT_TIMEOUT");
    }

    private byte[] loginPayload(long login,String password,byte[] cid) throws Exception {
        String url="web.metatrader.app";
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        out.write(u32(0));
        out.write(fixedUtf16(password,64));
        out.write(fixedUtf16("",128));
        out.write(cid);
        out.write(fixedUtf16("",64));
        out.write(fixedUtf16("",64));
        out.write(u64(0));
        out.write(fixedUtf16("",128));
        out.write(u32(url.length()));
        out.write(fixedUtf16(url,256));
        out.write(u64(login));
        out.write(new byte[160]);
        out.write(u64(0));
        return out.toByteArray();
    }

    private byte[] clientId() throws Exception {
        byte[] uniq=new byte[3]; random.nextBytes(uniq);
        int value=((uniq[0]&255)<<16)|((uniq[1]&255)<<8)|(uniq[2]&255);
        byte[] digest=MessageDigest.getInstance("SHA-1").digest(
            ("android;1;en-US;0x0;"+value).getBytes(StandardCharsets.UTF_8));
        return Arrays.copyOf(digest,16);
    }

    private byte[] inner(int cmd,byte[] payload) throws Exception {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        byte[] prefix=new byte[2]; random.nextBytes(prefix);
        out.write(prefix); out.write(u16(cmd)); out.write(payload);
        return out.toByteArray();
    }
    private static byte[] outer(byte[] body) throws Exception {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        out.write(u32(body.length)); out.write(u32(1)); out.write(body);
        return out.toByteArray();
    }
    private static byte[] crypt(byte[] key,byte[] data,int mode) throws Exception {
        Cipher cipher=Cipher.getInstance("AES/CBC/PKCS5Padding");
        cipher.init(mode,new SecretKeySpec(key,"AES"),new IvParameterSpec(new byte[16]));
        return cipher.doFinal(data);
    }
    private static byte[] fixedUtf16(String value,int size){
        byte[] src=value.getBytes(StandardCharsets.UTF_16LE);
        return Arrays.copyOf(src,size);
    }
    private static byte[] u16(int value){
        return ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN).putShort((short)value).array();
    }
    private static byte[] u32(int value){
        return ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(value).array();
    }
    private static byte[] u64(long value){
        return ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putLong(value).array();
    }
    private static String utf16(byte[] data,int offset,int size){
        int end=offset;
        for(int i=offset;i+1<offset+size;i+=2){
            if(data[i]==0&&data[i+1]==0){end=i;break;}
            end=i+2;
        }
        return new String(data,offset,Math.max(0,end-offset),StandardCharsets.UTF_16LE);
    }
    private static Result parseAccount(byte[] body,int loginCode) throws Exception {
        if(body.length<739) throw new java.io.IOException("MT5_DIRECT_ACCOUNT_SHORT");
        ByteBuffer b=ByteBuffer.wrap(body).order(ByteOrder.LITTLE_ENDIAN);
        int accountType=b.get()&255;
        int rights=b.getInt();
        b.getInt();
        double balance=b.getDouble();
        b.getDouble();
        String currency=utf16(body,b.position(),64); b.position(b.position()+64);
        b.getInt();
        b.getInt();
        b.position(b.position()+256);
        b.getShort();
        String server=utf16(body,b.position(),128);
        boolean demo=accountType==1&&"MetaQuotes-Demo".equals(server);
        if(!demo) throw new java.io.IOException("MT5_DIRECT_NOT_DEMO");
        return new Result(true,loginCode,server,currency,balance,
            (rights&4)==0,(rights&512)!=0);
    }
    private static byte[] hex(String value){
        byte[] out=new byte[value.length()/2];
        for(int i=0;i<out.length;i++) out[i]=(byte)Integer.parseInt(value.substring(i*2,i*2+2),16);
        return out;
    }
    private static final class Frame {
        final int code; final byte[] body;
        Frame(int code,byte[] body){this.code=code;this.body=body;}
    }

    @Override public void close(){
        try{if(socket!=null) socket.close(1000,"done");}catch(Exception ignored){}
        http.dispatcher().executorService().shutdown();
        frames.clear();
        key=INITIAL_KEY.clone();
    }
}
