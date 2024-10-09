import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import re
import pywhatkit as kit
import pygame
import sys
import os


#gspreadaccount@elite-conquest-409600.iam.gserviceaccount.com
origin = 'https://docs.google.com/spreadsheets/d/1DF5370Z4T6Mc1oBaGclq2LQWlK7R-YYc53awZBC9-a0/edit?pli=1&gid=872234949#gid=872234949'

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']

json_path = os.path.join(os.getcwd(), 'api_cred.json')
creds = Credentials.from_service_account_file(json_path, scopes=scope)


client = gspread.authorize(creds)

sheet = client.open_by_url(origin)
worksheets = sheet.worksheets()

def process_csv(wsheet):
    data = wsheet.get_all_records()
    df = pd.DataFrame(data)
    temp_list = list(df.columns)
    date = temp_list[1]  # get sheet date

    # rename cols
    df.columns.values[0] = "Product_Name"
    df.columns.values[1] = 'Quantity'
    df.columns.values[2] = 'Measurement Unit'

    df = df.dropna(how='all')
    df = df[(df != "").any(axis=1)]

    num = r'^\d+(\.\d+)?$'
    df2 = df[df['Quantity'].apply(lambda x: bool(re.match(num, str(x))))]

    # remove row without number in QTY column
    df3 = df2[(df2["Quantity"].isna() == False)]
    df3['concatenated'] = df3.apply(lambda row: f"- { row['Product_Name'] } { row['Quantity'] } { row['Measurement Unit'] }", axis=1)

    final_text = ""
    final_text = final_text + f"\nOrder for Supplier {wsheet.title} \n Date: {date}\n"
    for row in df3['concatenated']:
        final_text = final_text + "\n" + str(row)
    return final_text

message = ""
for ws in worksheets:
    message = message + process_csv(ws) + "\n"

def send_whatsapps(phone_number, message):
    try:
        kit.sendwhatmsg_instantly(phone_number, message)
        return 1
    except Exception as e:
        print(f"Failed to send message: {e}")
        return 0


pygame.init()

x_pixel = 680
y_pixel = 960
screen = pygame.display.set_mode((x_pixel, y_pixel))
pygame.display.set_caption("Filtered Order List")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230)

font = pygame.font.Font(None, 24)

# Input box for phone number
input_box = pygame.Rect(20, 860, 400, 50)
phone_number_input = ""
input_active = False

# Create a button (Rect object) and label
button_rect = pygame.Rect(450, 860, 200, 50)  # (x, y, width, height)
button_text = font.render("Send Message", True, BLACK)

# Render the body message text into lines
lines = message.split('\n')

def draw_text(text, x, y):
    text_surface = font.render(text, True, BLACK)
    screen.blit(text_surface, (x, y))


def draw_button():

    pygame.draw.rect(screen, LIGHT_BLUE, button_rect)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)

# Function to draw the input box for phone number
def draw_input_box():
    pygame.draw.rect(screen, LIGHT_BLUE, input_box, 2)
    input_text_surface = font.render(phone_number_input, True, WHITE)
    screen.blit(input_text_surface, (input_box.x + 10, input_box.y + 10))

# Main game loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle input box active state based on click location
            if input_box.collidepoint(event.pos):
                input_active = True
            else:
                input_active = False

            # Check if the send message button was clicked
            if button_rect.collidepoint(event.pos):
                if phone_number_input:
                    phone_number_input = '+6' + phone_number_input
                    print(f'Sending message to: {phone_number_input}')
                    send_whatsapps(phone_number_input, message)
                    print('Message sent')
                else:
                    print("No phone number entered")

        elif event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_BACKSPACE:
                phone_number_input = phone_number_input[:-1]
            elif event.unicode.isdigit() or event.unicode == '+':  # Allow digits and '+' symbol
                phone_number_input += event.unicode

    # Fill the screen with black
    screen.fill(BLACK)

    # Draw each line of text
    y_offset = 0  # Offset to move each line down
    for line in lines:
        text_surface = font.render(line, True, WHITE)
        text_rect = text_surface.get_rect(topleft=(20, 20 + y_offset))  # Position each line below the last one
        screen.blit(text_surface, text_rect)
        y_offset += font.get_height()  # Move the offset down by the height of the font

    # Draw the input box and the phone number input
    draw_input_box()

    # Draw the "Send Message" button
    draw_button()

    # Update the display
    pygame.display.flip()
