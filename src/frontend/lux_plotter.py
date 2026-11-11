import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# Paste your file path here as a string
csv_path = r"C:\Users\timlo\Desktop\Informatik\Nowcasting\Nowcasting project\solar-nowcasting\data\datasets\ground_truth\6_11_klar_sunset\light_log.csv"

# Read the log file
columns = ["filename", "timestamp", "lux", "full_spectrum", "ir"]
df = pd.read_csv(csv_path, header=None, names=columns)

# Convert Unix timestamp to UTC, then convert to local time (Europe/Vienna)
df["datetime"] = (
    pd.to_datetime(df["timestamp"], unit="s", utc=True)
    .dt.tz_convert("Europe/Vienna")
    .dt.tz_localize(None)
)

# Extract date for the header
log_date = df["datetime"].dt.date.iloc[0].strftime("%Y-%m-%d")

# Plot Lux over Time
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(
    df["datetime"], df["lux"], color="tab:blue", linewidth=1.5, label="Lux"
)

ax.set_title(
    f"Ambient Light (Lux) over Time (Local Time) | Date: {log_date}",
    fontsize=14,
    fontweight="bold",
)
ax.set_xlabel("Time of Day", fontsize=12)
ax.set_ylabel("Illuminance (Lux)", fontsize=12)

# Format X-axis: show only time with frequent intervals (every 30 minutes)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))

ax.grid(True, linestyle="--", alpha=0.6)
ax.legend(loc="upper right")
plt.tight_layout()

# Save the plot
plt.savefig("lux_over_time.png", dpi=300)
plt.show()