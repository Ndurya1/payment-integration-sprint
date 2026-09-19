Daraja stk- lipa na mpesa online. here is what i have learnt so far in a nutshell. 
# step 1: get an oauth token -
 here we use the consumer key and secret to generate an oauth key by base64 encoding them.
 
 # step 2: build timestamp, password and send stk push logic - 
 password is from base64 encoding the shortcode, passkey and timestamp. 
 timestamp in the password must match the top-level timestamp or else safaricom rejects the request.
then send the stk push.
immediately a responsecode is returned syncronously with code '0'.
this is not a transaction success code, it only shows that the stk prompt was queud to the customers phone.  
    
# step 3: callback. 
mpesa then sends a callback to your callback url.
this is an async process and has the resultcode you should trust. 
a resultCode of '0' indicates success.
any non-zero code shows failure. 1032- cancelled, 1- insufficient funds, 1037 - timeout. 

# important:
store checkoutRequestId and mpesaReceiptNumber with a unique constraint to avoid idempotency. 
use the stk push query and checkoutRequestId to ask for final status incase of timeout. 