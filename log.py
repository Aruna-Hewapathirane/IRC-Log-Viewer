from datetime import datetime
import socket
import ssl
import time

# Configuration
SERVER = "irc.libera.chat"
PORT = 6697  # TLS/SSL port
NICK = "history-bot"  # Change to a unique nickname
CHANNEL = "#pascal"
#CHANNEL = "#aruna"
LOG_FILE = "pascal.log"


def log_line(text: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #entry = f"[{timestamp}] {text}\n"
    entry = f"{timestamp} {text}\n"
    print(entry, end="")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def run_logger() -> None:
    context = ssl.create_default_context()

    while True:
        try:
            log_line(f"--- Connecting to {SERVER}:{PORT} ---")
            raw_sock = socket.create_connection((SERVER, PORT), timeout=300)
            irc = context.wrap_socket(raw_sock, server_hostname=SERVER)

            def send(cmd: str) -> None:
                irc.sendall(f"{cmd}\r\n".encode("utf-8"))

            send(f"NICK {NICK}")
            send(f"USER {NICK} 0 * :Python IRC Logger")

            buffer = ""
            while True:
                data = irc.recv(4096)
                if not data:
                    raise ConnectionError("Connection closed by server.")

                buffer += data.decode("utf-8", errors="replace")

                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    if line.startswith("PING "):
                        send("PONG " + line[5:])
                        continue

                    parts = line.split(" ")
                    if len(parts) > 1 and parts[1] == "001":
                        log_line(f"--- Connected. Joining {CHANNEL} ---")
                        send(f"JOIN {CHANNEL}")
                    elif (
                        len(parts) > 3
                        and parts[1] == "PRIVMSG"
                        and parts[2].lower() == CHANNEL.lower()
                    ):
                        sender = parts[0][1:].split("!")[0]
                        message = line.split(" :", 1)[1]
                        if message.startswith("\x01ACTION ") and message.endswith("\x01"):
                            # /me message: log it the way IRC clients show it
                            log_line(f"* {sender} {message[8:-1]}")
                        elif message.startswith("\x01"):
                            pass  # other CTCP requests (VERSION, PING...): not chat, skip
                        else:
                            log_line(f"<{sender}> {message}")
                    elif len(parts) > 1 and parts[1] in ("JOIN", "PART", "QUIT"):
                        sender = parts[0][1:].split("!")[0]
                        log_line(f"* {sender} ({parts[1]})")
                    elif len(parts) > 2 and parts[1] == "NICK":
                        sender = parts[0][1:].split("!")[0]
                        log_line(f"* {sender} (NICK {parts[2].lstrip(':')})")
                    elif (
                        len(parts) > 3
                        and parts[1] == "KICK"
                        and parts[2].lower() == CHANNEL.lower()
                    ):
                        kicker = parts[0][1:].split("!")[0]
                        log_line(f"* {parts[3]} (KICK by {kicker})")

        except KeyboardInterrupt:
            log_line("--- Logger stopped by user ---")
            break
        except Exception as e:
            log_line(f"--- Error: {e}. Reconnecting in 15 seconds... ---")
            time.sleep(15)


if __name__ == "__main__":
    run_logger()
