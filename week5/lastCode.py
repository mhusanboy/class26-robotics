import time

class Program():
  def execMain(self):
    script.removeFile("motor_data.txt")
    power = -100
    while power <= 100:
      brick.encoder("E4").reset()
      st = ""
      t = 0
      brick.motor("M4").setPower(power)
      t0 = time.time() * 1000
      while t < 2000:
        theta_l = brick.encoder("E4").read()
        t = time.time() * 1000 - t0
        st = st + str(power) + "," + str(theta_l) + "," + str(t) + "\n"
        script.wait(5)
      brick.motor("M4").setPower(0)
      script.writeToFile("motor_data.txt", st)
      script.wait(1000)
      power = power + 5
    brick.stop()

def main():
  program = Program()
  program.execMain()

if __name__ == "__main__":
  main()
