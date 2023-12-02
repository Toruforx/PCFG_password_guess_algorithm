import matplotlib.pyplot as plt

def draw_result(path, c):
    true_guess = [0]
    total_guess = [0]
    flag = 0
    fpath = path + ".txt"
    with open(fpath, "r") as f:
        for line in f:
            if flag == 0:
                flag = 1
                continue
            l = line.strip().split('/', 1)
            true_guess.append(int(l[0].strip()))
            total_guess.append(int(l[1].strip()))
    plt.plot(total_guess, true_guess, marker='*', color = c, label = path)

def main():
    plt.xlim(0,20000000)
    plt.ylim(0,10000)
    draw_result('ori-dic-0294', 'red')
    draw_result('new-order-1', 'blue')
    draw_result('new-order-2', 'yellow')
    draw_result('new-order-3', 'green')
    draw_result('new-order-4', 'black')
    plt.legend()
    plt.xlabel('total_guess')
    plt.ylabel('true_guess')
    plt.show()

if __name__ == "__main__":
    main()
    