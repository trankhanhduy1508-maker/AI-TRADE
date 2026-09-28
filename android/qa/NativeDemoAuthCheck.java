import vn.cws.aitrade.NativeDemoAuth;
public class NativeDemoAuthCheck {
  public static void main(String[] args) {
    String verifier=NativeDemoAuth.randomUrlSafe(64);
    String nonce=NativeDemoAuth.randomUrlSafe(24);
    String challenge=NativeDemoAuth.challenge(verifier);
    if(verifier.length()!=86 || nonce.length()!=32 || challenge.length()!=43)throw new AssertionError();
    String u=NativeDemoAuth.authorizeUrl(nonce,verifier);
    if(!u.startsWith("https://oziktadfeenydvgobudr.supabase.co/auth/v1/authorize?provider=google")|| !u.contains("code_challenge_method=s256"))throw new AssertionError();
    if(!NativeDemoAuth.matchesCallback("vn.cws.aitrade","auth","/callback/"+nonce,nonce))throw new AssertionError();
    if(NativeDemoAuth.matchesCallback("vn.cws.aitrade","auth","/callback/other",nonce))throw new AssertionError();
    if(NativeDemoAuth.matchesCallback("vn.cws.aitrade","evil","/callback/"+nonce,nonce))throw new AssertionError();
    if(NativeDemoAuth.matchesCallback("http","auth","/callback/"+nonce,nonce))throw new AssertionError();
    boolean blocked=false;
    try{NativeDemoAuth.challenge("short");}catch(IllegalArgumentException e){blocked=true;}
    if(!blocked)throw new AssertionError("invalid PKCE not blocked");
    System.out.println("PASS: Java PKCE verifier, SHA-256 challenge, URL and callback nonce checks (8 assertions)");
  }
}
