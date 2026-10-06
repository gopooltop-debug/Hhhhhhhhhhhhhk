using System;
using System.Windows.Forms;

namespace Практика_4
{
    public partial class Form1 : Form
    {
        const int SmallSize = 80;       // «Маленький»
        const int BigSize = 150;        // «Большой»
        const int SlowInterval = 100;   // «Медленно»: интервал таймера, мс
        const int FastInterval = 30;    // «Быстро»

        // Объект, которым управляем: x, y, размер, направление.
        Pic myperson = new Pic(200, 100, SmallSize, 1);

        public Form1()
        {
            InitializeComponent();

            // Рисунки у пунктов «Вид» и контекстного меню — те же, что в imageList1.
            персонаж1ToolStripMenuItem.Image = imageList1.Images[0];
            персонаж2ToolStripMenuItem.Image = imageList1.Images[1];
            персонаж3ToolStripMenuItem.Image = imageList1.Images[2];
            контекстПерсонаж1ToolStripMenuItem.Image = imageList1.Images[0];
            контекстПерсонаж2ToolStripMenuItem.Image = imageList1.Images[1];
            контекстПерсонаж3ToolStripMenuItem.Image = imageList1.Images[2];

            // Начальное состояние: влево, маленький, быстро.
            SetDir(1);
            SetSize(SmallSize);
            SetSpeed(FastInterval);
        }

        // Таймер: на каждом тике объект сдвигается и перерисовывается.
        private void timer1_Tick(object sender, EventArgs e)
        {
            myperson.Draw(pictureBox1);
        }

        // ===================== Меню «Направление» =====================

        void SetDir(int d)
        {
            myperson.Dir = d;

            // Галочка у текущего пункта меню и «нажатая» кнопка на панели.
            влевоToolStripMenuItem.Checked = d == 1;
            вправоToolStripMenuItem.Checked = d == 2;
            вверхToolStripMenuItem.Checked = d == 3;
            внизToolStripMenuItem.Checked = d == 4;
            toolStripButton1.Checked = d == 1;
            toolStripButton2.Checked = d == 2;
            toolStripButton3.Checked = d == 3;
            toolStripButton4.Checked = d == 4;
        }

        private void влевоToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetDir(1);
        }

        private void вправоToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetDir(2);
        }

        private void вверхToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetDir(3);
        }

        private void внизToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetDir(4);
        }

        // ===================== Меню «Вид» =====================

        void SetView(int index)
        {
            pictureBox1.Image = imageList1.Images[index];   // рисунок берём из imageList

            персонаж1ToolStripMenuItem.Checked = index == 0;
            персонаж2ToolStripMenuItem.Checked = index == 1;
            персонаж3ToolStripMenuItem.Checked = index == 2;
            контекстПерсонаж1ToolStripMenuItem.Checked = index == 0;
            контекстПерсонаж2ToolStripMenuItem.Checked = index == 1;
            контекстПерсонаж3ToolStripMenuItem.Checked = index == 2;
        }

        private void персонаж1ToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetView(0);
        }

        private void персонаж2ToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetView(1);
        }

        private void персонаж3ToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetView(2);
        }

        // ===================== Меню «Размер» =====================

        void SetSize(int sz)
        {
            myperson.Size = sz;

            большойToolStripMenuItem.Checked = sz == BigSize;
            маленькийToolStripMenuItem.Checked = sz == SmallSize;
        }

        private void большойToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetSize(BigSize);
        }

        private void маленькийToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetSize(SmallSize);
        }

        // ===================== Меню «Скорость» =====================

        void SetSpeed(int interval)
        {
            timer1.Interval = interval;   // чем меньше интервал, тем быстрее движение

            медленноToolStripMenuItem.Checked = interval == SlowInterval;
            быстроToolStripMenuItem.Checked = interval == FastInterval;

            // Выпадающий список на панели показывает ту же скорость, что и меню.
            toolStripComboBox1.SelectedIndex = interval == SlowInterval ? 0 : 1;
        }

        private void медленноToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetSpeed(SlowInterval);
        }

        private void быстроToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SetSpeed(FastInterval);
        }

        // ===================== Меню «Выход» =====================

        private void выходToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Close();
        }

        // ============ Контекстное меню картинки (задача 3) ============
        // Повторяет пункты меню «Вид»: просто «нажимает» их.

        private void контекстПерсонаж1ToolStripMenuItem_Click(object sender, EventArgs e)
        {
            персонаж1ToolStripMenuItem.PerformClick();
        }

        private void контекстПерсонаж2ToolStripMenuItem_Click(object sender, EventArgs e)
        {
            персонаж2ToolStripMenuItem.PerformClick();
        }

        private void контекстПерсонаж3ToolStripMenuItem_Click(object sender, EventArgs e)
        {
            персонаж3ToolStripMenuItem.PerformClick();
        }

        // ============ Панель инструментов (задача 4) ============
        // Обработчики панели вызывают пункты главного меню.

        private void toolStripButton1_Click(object sender, EventArgs e)
        {
            влевоToolStripMenuItem.PerformClick();
        }

        private void toolStripButton2_Click(object sender, EventArgs e)
        {
            вправоToolStripMenuItem.PerformClick();
        }

        private void toolStripButton3_Click(object sender, EventArgs e)
        {
            вверхToolStripMenuItem.PerformClick();
        }

        private void toolStripButton4_Click(object sender, EventArgs e)
        {
            внизToolStripMenuItem.PerformClick();
        }

        private void toolStripComboBox1_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (toolStripComboBox1.SelectedIndex == 0)
                медленноToolStripMenuItem.PerformClick();
            else
                быстроToolStripMenuItem.PerformClick();
        }
    }
}
