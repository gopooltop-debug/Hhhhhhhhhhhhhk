using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows.Forms;

namespace Практика_9
{
    public partial class Form1 : Form
    {
        // Для передачи записи между основной формой и окнами диалога.
        static public Record Rec;

        // Вся таблица: список записей. Для начала инициализирован данными 5 строк.
        List <Record> Table = new List <Record>()
        {   new Record("Максим Савинков", new DateTime(2003, 10, 22), "Клоун", "Цирк", 50000),
            new Record("Илья Клюшин", new DateTime(2004, 2, 10), "Сантехник", "ЖКХ", 40000),
            new Record("Иван Иванов", new DateTime(1990, 5, 15), "Инженер", "ИТ-отдел", 80000),
            new Record("Петр Петров", new DateTime(1985, 10, 10), "Директор", "Администрация", 150000),
            new Record("Анна Анненкова", new DateTime(1978, 7, 2), "Учитель", "Школа", 45000)
        };

        // Состояния таблицы до каждого изменения — для «Отмены действия».
        Stack<List<Record>> undoStack = new Stack<List<Record>>();

        const string AppTitle = "Табличное представление данных";

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            Redraw();
        }

        // Отрисовка обновлённого грида: DataSource нельзя изменить, его снимают и назначают снова.
        // select — номер строки, которую выделить после перерисовки.
        public void Redraw(int select = -1)
        {
            dataGridView1.DataSource = null;
            dataGridView1.AutoGenerateColumns = true;
            dataGridView1.DataSource = Table;

            // Порядок следования колонок и заголовки.
            SetColumn("Name", 0, "Имя", null, 30);
            SetColumn("BirthDate", 1, "Дата рождения", "dd.MM.yyyy", 15);
            SetColumn("Profession", 2, "Должность", null, 22);
            SetColumn("Department", 3, "Отдел", null, 18);
            SetColumn("Money", 4, "Оклад, руб.", "N2", 15);
            dataGridView1.Columns["Money"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            dataGridView1.Columns["BirthDate"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;

            dataGridView1.ClearSelection();
            if (Table.Count > 0)
            {
                if (select < 0) select = 0;
                if (select >= Table.Count) select = Table.Count - 1;
                dataGridView1.CurrentCell = dataGridView1.Rows[select].Cells["Name"];
                dataGridView1.Rows[select].Selected = true;
            }
            ShowCurrent();
            отменаToolStripMenuItem.Enabled = undoStack.Count > 0;
        }

        void SetColumn(string property, int index, string header, string format, float weight)
        {
            DataGridViewColumn column = dataGridView1.Columns[property];
            column.DataPropertyName = property;   // Название поля записи
            column.HeaderText = header;           // Заголовок столбца
            column.DisplayIndex = index;
            column.FillWeight = weight;
            column.SortMode = DataGridViewColumnSortMode.NotSortable;
            if (format != null)
                column.DefaultCellStyle.Format = format;
        }

        // Показать текущую запись в текстовом поле внизу формы.
        void ShowCurrent()
        {
            if (dataGridView1.CurrentRow == null || Table.Count == 0)
            {
                textBox1.Text = "";
                return;
            }
            int current = dataGridView1.CurrentRow.Index;
            // Извлечь данные из таблицы по номеру:
            Record Tmp = new Record(Table[current].Name, Table[current].BirthDate,
                Table[current].Profession, Table[current].Department, Table[current].Money);
            // Показать как строку:
            textBox1.Text = Tmp.ToString();
        }

        private void dataGridView1_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            ShowCurrent();
        }

        // Переход по записям стрелками тоже обновляет текстовое поле.
        private void dataGridView1_SelectionChanged(object sender, EventArgs e)
        {
            ShowCurrent();
        }

        // Двойной щелчок по строке — изменить запись.
        private void dataGridView1_CellDoubleClick(object sender, DataGridViewCellEventArgs e)
        {
            if (e.RowIndex >= 0)
                изменитьToolStripMenuItem_Click(sender, e);
        }

        // Enter — изменить, Delete — удалить.
        private void dataGridView1_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                изменитьToolStripMenuItem_Click(sender, e);
                e.Handled = true;
            }
            else if (e.KeyCode == Keys.Delete)
            {
                удалитьToolStripMenuItem_Click(sender, e);
                e.Handled = true;
            }
        }

        // Запомнить состояние таблицы перед изменением.
        void SaveUndo()
        {
            undoStack.Push(new List<Record>(Table));
        }

        // Номер текущей строки или -1, если выбирать нечего.
        int CurrentIndex()
        {
            if (Table.Count == 0 || dataGridView1.CurrentRow == null)
            {
                MessageBox.Show("Таблица пуста или запись не выбрана.", AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                return -1;
            }
            return dataGridView1.CurrentRow.Index;
        }

        #region Правка: добавить, изменить, удалить, отмена

        private void добавитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Add Dialog = new Add();
            // Показать диалог.
            if (Dialog.ShowDialog(this) == DialogResult.OK)
            {
                SaveUndo();
                Table.Add(Rec);          // Получена запись, добавлена в Table.
                Redraw(Table.Count - 1);
            }
        }

        private void изменитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            int current = CurrentIndex();
            if (current < 0)
                return;
            // Извлечь в переменную static public Record Rec и передать в диалог.
            Rec = Table[current];
            Change Dialog = new Change();
            // Если DialogResult вернул запись, то изменённую запись вставить в таблицу по положению current.
            if (Dialog.ShowDialog(this) == DialogResult.OK)
            {
                SaveUndo();
                Table[current] = Rec;
                Redraw(current);
            }
        }

        private void удалитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            int current = CurrentIndex();
            if (current < 0)
                return;

            // Если выделено несколько строк (например, «Выделить все») — удаляем их все.
            List<int> rows = dataGridView1.SelectedRows.Cast<DataGridViewRow>()
                .Select(r => r.Index).OrderByDescending(i => i).ToList();
            if (rows.Count <= 1)
                rows = new List<int> { current };

            string question;
            if (rows.Count == 1)
            {
                Rec = Table[current];
                question = "Попытка удалить запись:\n" + Rec.ToString();
            }
            else
                question = "Попытка удалить выделенные записи: " + rows.Count + " шт.";

            var result = MessageBox.Show(question, "Удаление",
                MessageBoxButtons.OKCancel, MessageBoxIcon.Question);
            if (result != DialogResult.OK)
                return;

            SaveUndo();
            foreach (int i in rows)
                Table.RemoveAt(i);
            Redraw(rows.Last());
        }

        private void отменаToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (undoStack.Count == 0)
                return;
            int current = dataGridView1.CurrentRow == null ? 0 : dataGridView1.CurrentRow.Index;
            Table = undoStack.Pop();
            Redraw(current);
        }

        private void выделитьВсеToolStripMenuItem_Click(object sender, EventArgs e)
        {
            dataGridView1.SelectAll();
            dataGridView1.Focus();
        }

        #endregion

        #region Операции с данными: сортировка, итоги

        void SortTable(Comparison<Record> comparison)
        {
            if (Table.Count < 2)
                return;
            SaveUndo();
            Table.Sort(comparison);
            Redraw();
        }

        private void поИмениToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SortTable((a, b) => string.Compare(a.Name, b.Name, StringComparison.CurrentCulture));
        }

        private void поДатеРожденияToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SortTable((a, b) => a.BirthDate.CompareTo(b.BirthDate));
        }

        private void поОкладуToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SortTable((a, b) => b.Money.CompareTo(a.Money));
        }

        private void итогиToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (Table.Count == 0)
            {
                MessageBox.Show("Таблица пуста.", AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            StringBuilder sb = new StringBuilder();
            var groups = Table.GroupBy(p => p.Department).OrderBy(g => g.Key);
            foreach (var g in groups)
                sb.AppendLine(string.Format("{0}: {1} чел., сумма {2:N2}, средний оклад {3:N2} руб.",
                    g.Key, g.Count(), g.Sum(p => p.Money), g.Average(p => p.Money)));
            sb.AppendLine();
            sb.AppendLine(string.Format("Всего: {0} чел., фонд оплаты {1:N2} руб.", Table.Count, Table.Sum(p => p.Money)));
            sb.AppendLine(string.Format("Средний оклад: {0:N2} руб.", Table.Average(p => p.Money)));
            Record max = Table.OrderByDescending(p => p.Money).First();
            sb.AppendLine(string.Format("Наибольший оклад: {0} ({1:N2} руб.)", max.Name, max.Money));
            MessageBox.Show(sb.ToString(), "Итоги по отделам", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        #endregion

        private void оПрограммеToolStripMenuItem_Click(object sender, EventArgs e)
        {
            MessageBox.Show(
                "Практическое задание 9: прикладная задача на списке.\n" +
                "Таблица сотрудников: имя, дата рождения, должность, отдел, оклад.\n\n" +
                "Данные хранятся в List<Record> и показываются в DataGridView.\n\n" +
                "Горячие клавиши:\n" +
                "Ctrl+A — добавить, Ctrl+E — изменить, Ctrl+D — удалить\n" +
                "Ctrl+Z — отмена действия, Ctrl+Shift+A — выделить все\n" +
                "Ctrl+T — итоги по отделам",
                "О программе", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void выходToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Close();
        }
    }
}
