import streamlit as st
import cv2
import numpy as np
import io

def encode_message(img, msg, password):
    # Combine password and message with a separator
    # Format: PASSWORD + "||" + MESSAGE + "#####"
    full_msg = password + "||" + msg + "#####"
    
    msg_len = len(full_msg)
    max_bytes = img.shape[0] * img.shape[1] * 3 // 8
    
    if msg_len > max_bytes:
        raise ValueError("Message is too long to encode in this image!")

    # Convert to binary
    msg_bin = ''.join(format(ord(i), '08b') for i in full_msg)
    data_index = 0
    
    encoded_img = img.copy()
    flat_img = encoded_img.flatten()
    
    for i in range(len(flat_img)):
        if data_index < len(msg_bin):
            # FIX: Use 254 (11111110) instead of ~1 (-2) to prevent uint8 error
            flat_img[i] = (flat_img[i] & 254) | int(msg_bin[data_index])
            data_index += 1
        else:
            break
            
    encoded_img = flat_img.reshape(img.shape)
    return encoded_img

def decode_message(img, input_password):
    msg_bin = ""
    flat_img = img.flatten()
    
    for pixel_val in flat_img:
        msg_bin += str(pixel_val & 1)

    extracted_text = ""
    # Convert binary to chars 8 bits at a time
    for i in range(0, len(msg_bin), 8):
        byte = msg_bin[i:i + 8]
        if len(byte) == 8:
            char = chr(int(byte, 2))
            extracted_text += char
            
            # Stop if we find the end delimiter
            if extracted_text.endswith("#####"):
                clean_text = extracted_text[:-5] # Remove #####
                
                # Split into Password and Message
                if "||" in clean_text:
                    stored_pass, stored_msg = clean_text.split("||", 1)
                    
                    if input_password == stored_pass:
                        return f"✅ Success! Message: {stored_msg}"
                    else:
                        return "❌ Error: Incorrect Passcode."
                else:
                    return "❌ Error: No password protection found in this image."
                
    return "❌ Error: No hidden message found."

# --- UI SETUP ---
st.title("🔐 Steganography: Secure Data Hiding")
st.write("Hide secret messages inside images with password protection.")

tab1, tab2 = st.tabs(["🔒 Encrypt", "🔓 Decrypt"])

# --- ENCRYPTION TAB ---
with tab1:
    st.header("Hide a Message")
    uploaded_file = st.file_uploader("Upload Image (PNG/JPG)", type=['png', 'jpg', 'jpeg'], key="enc_file")
    
    if uploaded_file:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        st.image(uploaded_file, caption="Original", width=300)
        
        msg = st.text_area("Secret Message")
        password = st.text_input("Set Passcode", type="password", key="enc_pass")
        
        if st.button("Encode & Save"):
            if not msg or not password:
                st.error("Message and Passcode are required!")
            else:
                try:
                    res_img = encode_message(img, msg, password)
                    is_success, buffer = cv2.imencode(".png", res_img)
                    
                    st.success("Message Hidden! Download your image below.")
                    st.download_button(
                        label="Download Encrypted Image",
                        data=io.BytesIO(buffer),
                        file_name="secret_image.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

# --- DECRYPTION TAB ---
with tab2:
    st.header("Reveal Message")
    dec_file = st.file_uploader("Upload Encrypted Image (PNG)", type=['png'], key="dec_file")
    
    if dec_file:
        file_bytes = np.asarray(bytearray(dec_file.read()), dtype=np.uint8)
        dec_img = cv2.imdecode(file_bytes, 1)
        st.image(dec_file, caption="Encrypted Image", width=300)
        
        dec_pass = st.text_input("Enter Passcode", type="password", key="dec_pass")
        
        if st.button("Decode"):
            if not dec_pass:
                st.warning("Please enter the passcode.")
            else:
                result = decode_message(dec_img, dec_pass)
                if "✅" in result:
                    st.success(result)
                else:
                    st.error(result)
