using System.Windows.Forms;

namespace Практика_4
{
    // Объект «картинка», которым управляет форма.
    // Форма только меняет свойства объекта (Dir, Size), а объект сам
    // двигается и отрисовывает себя на PictureBox в методе Draw.
    public class Pic
    {
        int x = 200, y = 200;   // Положение (левый верхний угол) внутри контейнера
        int dir = 1;            // Направление: 1 - влево, 2 - вправо, 3 - вверх, 4 - вниз
        int size = 80;          // Размер (ширина = высота)
        int step = 3;           // На сколько пикселей сдвигаемся за один тик таймера

        int W, H;               // Ширина и высота контейнера, в котором двигается картинка

        public int X { get { return x; } set { x = value; } }
        public int Y { get { return y; } set { y = value; } }
        public int Dir { get { return dir; } set { dir = value; } }
        public int Size { get { return size; } set { size = value; } }

        public Pic(int xx = 200, int yy = 200, int Sz = 80, int D = 1)
        {
            x = xx;
            y = yy;
            dir = D;
            size = Sz;
        }

        // Методы движения. У края контейнера картинка останавливается (задача 2).
        public void Left()
        {
            if (x > step)
                x -= step;
            else
                x = 0;              // иначе стоять у левого края
        }
        public void Right()
        {
            if (x < W - size - step)
                x += step;
            else
                x = W - size;       // иначе стоять у правого края
        }
        public void Up()
        {
            if (y > step)
                y -= step;
            else
                y = 0;              // иначе стоять у верхнего края
        }
        public void Down()
        {
            if (y < H - size - step)
                y += step;
            else
                y = H - size;       // иначе стоять у нижнего края
        }

        // Если картинку увеличили или окно уменьшили — возвращаем её внутрь контейнера.
        void KeepInside()
        {
            if (x > W - size) x = W - size;
            if (y > H - size) y = H - size;
            if (x < 0) x = 0;
            if (y < 0) y = 0;
        }

        // Метод отражения: узнать размер контейнера,
        //                  выбрать направление и изменить координату,
        //                  изменить размер,
        //                  отрисовать.
        public void Draw(PictureBox Pb)
        {
            // Размер контейнера берём у того, в ком лежит PictureBox (у нас это panel1).
            // Создавать здесь new Form1() нельзя: каждый тик создавалась бы новая
            // скрытая форма — программа тормозит и съедает память.
            W = Pb.Parent.ClientSize.Width;
            H = Pb.Parent.ClientSize.Height;

            switch (dir)
            {
                case 1: { Left(); break; }
                case 2: { Right(); break; }
                case 3: { Up(); break; }
                case 4: { Down(); break; }
            }
            KeepInside();

            // Одной командой вместо Left/Top/Width/Height — так картинка не мерцает.
            Pb.SetBounds(x, y, size, size);
        }
    }
}
