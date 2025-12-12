import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

def encode_message(img, msg):
    # Add a delimiter so we know where the message ends
    msg += "#####" 
    
    msg_len = len(msg)
    max_bytes = img.shape[0] * img.shape[1] * 3 // 8
    
    if msg_len > max_bytes:
        raise ValueError("Message is too long to encode in this image!")

    # Convert to binary
    msg_bin = ''.join(format(ord(i), '08b') for i in msg)
    data_index = 0
    
    # We work on a copy to avoid modifying the original
    encoded_img = img.copy()
    
    flat_img = encoded_img.flatten()
    
    for i in range(len(flat_img)):
        if data_index < len(msg_bin):
            # Modify LSB
            flat_img[i] = (flat_img[i] & ~1) | int(msg_bin[data_index])
            data_index += 1
        else:
            break
            
    encoded_img = flat_img.reshape(img.shape)
    return encoded_img

def decode_message(img):
    msg_bin = ""
    flat_img = img.flatten()
    
    # Read LSBs
    for pixel_val in flat_img:
        msg_bin += str(pixel_val & 1)

    message = ""
    # Convert binary to chars 8 bits at a time
    for i in range(0, len(msg_bin), 8):
        byte = msg_bin[i:i + 8]
        if len(byte) == 8:
            char = chr(int(byte, 2))
            message += char
            # Check for our delimiter
            if message.endswith("#####"):
                return message[:-5] # Return message without delimiter
                
    return "No hidden message found (or message corrupted)."

# --- STREAMLIT UI ---
st.title("🔐 Steganography: Hide Data in Images")
st.write("Securely hide secret messages inside standard images.")

tab1, tab2 = st.tabs(["🔒 Encrypt (Hide)", "🔓 Decrypt (Reveal)"])

with tab1:
    st.header("Hide a Message")
    uploaded_file = st.file_uploader("Upload an Image", type=['png', 'jpg', 'jpeg'], key="encrypt_upload")
    
    if uploaded_file is not None:
        # Convert file to opencv image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        # Display original
        st.image(uploaded_file, caption="Original Image", width=300)
        
        msg = st.text_area("Enter Secret Message:")
        password = st.text_input("Set a Passcode (Optional)", type="password", key="enc_pass")
        
        if st.button("Encode & Save"):
            if not msg:
                st.error("Please enter a message.")
            else:
                try:
                    # In a real scenario, you'd encrypt the text with the password first.
                    # For this demo, we just require the user to know it later.
                    encoded_img = encode_message(img, msg)
                    
                    # Convert back to PNG for saving (JPG loses data due to compression!)
                    is_success, buffer = cv2.imencode(".png", encoded_img)
                    io_buf = io.BytesIO(buffer)
                    
                    st.success("Message hidden successfully!")
                    st.download_button(
                        label="Download Encrypted Image",
                        data=io_buf,
                        file_name="secret_image.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.header("Reveal a Message")
    dec_file = st.file_uploader("Upload Encrypted Image (PNG only)", type=['png'], key="decrypt_upload")
    
    if dec_file is not None:
        file_bytes = np.asarray(bytearray(dec_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        st.image(dec_file, caption="Uploaded Image", width=300)
        
        pas_input = st.text_input("Enter Passcode", type="password", key="dec_pass")
        
        if st.button("Decode Message"):
            # NOTE: In this simple demo, we rely on the user knowing the correct password.
            # Real steganography tools encrypt the payload payload.
            if pas_input: 
                hidden_msg = decode_message(img)
                st.success("Decoded Message:")
                st.code(hidden_msg)
            else:
                st.warning("Please enter the passcode used during encryption.")
