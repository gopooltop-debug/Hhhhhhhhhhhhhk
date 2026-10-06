namespace Практика_4
{
    partial class Form1
    {
        /// <summary>
        /// Обязательная переменная конструктора.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Освободить все используемые ресурсы.
        /// </summary>
        /// <param name="disposing">истинно, если управляемый ресурс должен быть удален; иначе ложно.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Код, автоматически созданный конструктором форм Windows

        /// <summary>
        /// Требуемый метод для поддержки конструктора — не изменяйте
        /// содержимое этого метода с помощью редактора кода.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Form1));
            this.pictureBox1 = new System.Windows.Forms.PictureBox();
            this.contextMenuStrip1 = new System.Windows.Forms.ContextMenuStrip(this.components);
            this.контекстПерсонаж1ToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.контекстПерсонаж2ToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.контекстПерсонаж3ToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.timer1 = new System.Windows.Forms.Timer(this.components);
            this.menuStrip1 = new System.Windows.Forms.MenuStrip();
            this.направлениеToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.влевоToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.вправоToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.вверхToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.внизToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.видToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.персонаж1ToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.персонаж2ToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.персонаж3ToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.размерToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.большойToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.маленькийToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.скоростьToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.медленноToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.быстроToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.выходToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.toolStrip1 = new System.Windows.Forms.ToolStrip();
            this.toolStripButton1 = new System.Windows.Forms.ToolStripButton();
            this.toolStripButton2 = new System.Windows.Forms.ToolStripButton();
            this.toolStripButton3 = new System.Windows.Forms.ToolStripButton();
            this.toolStripButton4 = new System.Windows.Forms.ToolStripButton();
            this.toolStripSeparator1 = new System.Windows.Forms.ToolStripSeparator();
            this.toolStripComboBox1 = new System.Windows.Forms.ToolStripComboBox();
            this.imageList1 = new System.Windows.Forms.ImageList(this.components);
            this.panel1 = new System.Windows.Forms.Panel();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).BeginInit();
            this.contextMenuStrip1.SuspendLayout();
            this.menuStrip1.SuspendLayout();
            this.toolStrip1.SuspendLayout();
            this.panel1.SuspendLayout();
            this.SuspendLayout();
            //
            // pictureBox1
            //
            this.pictureBox1.BackColor = System.Drawing.Color.Transparent;
            this.pictureBox1.ContextMenuStrip = this.contextMenuStrip1;
            this.pictureBox1.Image = ((System.Drawing.Image)(resources.GetObject("pictureBox1.Image")));
            this.pictureBox1.Location = new System.Drawing.Point(200, 100);
            this.pictureBox1.Name = "pictureBox1";
            this.pictureBox1.Size = new System.Drawing.Size(80, 80);
            this.pictureBox1.SizeMode = System.Windows.Forms.PictureBoxSizeMode.Zoom;
            this.pictureBox1.TabIndex = 0;
            this.pictureBox1.TabStop = false;
            //
            // contextMenuStrip1
            //
            this.contextMenuStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.контекстПерсонаж1ToolStripMenuItem,
            this.контекстПерсонаж2ToolStripMenuItem,
            this.контекстПерсонаж3ToolStripMenuItem});
            this.contextMenuStrip1.Name = "contextMenuStrip1";
            this.contextMenuStrip1.Size = new System.Drawing.Size(181, 70);
            //
            // контекстПерсонаж1ToolStripMenuItem
            //
            this.контекстПерсонаж1ToolStripMenuItem.Name = "контекстПерсонаж1ToolStripMenuItem";
            this.контекстПерсонаж1ToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.контекстПерсонаж1ToolStripMenuItem.Text = "Лосяш";
            this.контекстПерсонаж1ToolStripMenuItem.Click += new System.EventHandler(this.контекстПерсонаж1ToolStripMenuItem_Click);
            //
            // контекстПерсонаж2ToolStripMenuItem
            //
            this.контекстПерсонаж2ToolStripMenuItem.Name = "контекстПерсонаж2ToolStripMenuItem";
            this.контекстПерсонаж2ToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.контекстПерсонаж2ToolStripMenuItem.Text = "Пин";
            this.контекстПерсонаж2ToolStripMenuItem.Click += new System.EventHandler(this.контекстПерсонаж2ToolStripMenuItem_Click);
            //
            // контекстПерсонаж3ToolStripMenuItem
            //
            this.контекстПерсонаж3ToolStripMenuItem.Name = "контекстПерсонаж3ToolStripMenuItem";
            this.контекстПерсонаж3ToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.контекстПерсонаж3ToolStripMenuItem.Text = "Крош";
            this.контекстПерсонаж3ToolStripMenuItem.Click += new System.EventHandler(this.контекстПерсонаж3ToolStripMenuItem_Click);
            //
            // timer1
            //
            this.timer1.Enabled = true;
            this.timer1.Interval = 30;
            this.timer1.Tick += new System.EventHandler(this.timer1_Tick);
            //
            // menuStrip1
            //
            this.menuStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.направлениеToolStripMenuItem,
            this.видToolStripMenuItem,
            this.размерToolStripMenuItem,
            this.скоростьToolStripMenuItem,
            this.выходToolStripMenuItem});
            this.menuStrip1.Location = new System.Drawing.Point(0, 0);
            this.menuStrip1.Name = "menuStrip1";
            this.menuStrip1.Size = new System.Drawing.Size(800, 24);
            this.menuStrip1.TabIndex = 1;
            this.menuStrip1.Text = "menuStrip1";
            //
            // направлениеToolStripMenuItem
            //
            this.направлениеToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.влевоToolStripMenuItem,
            this.вправоToolStripMenuItem,
            this.вверхToolStripMenuItem,
            this.внизToolStripMenuItem});
            this.направлениеToolStripMenuItem.Name = "направлениеToolStripMenuItem";
            this.направлениеToolStripMenuItem.Size = new System.Drawing.Size(93, 20);
            this.направлениеToolStripMenuItem.Text = "&Направление";
            //
            // влевоToolStripMenuItem
            //
            this.влевоToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("влевоToolStripMenuItem.Image")));
            this.влевоToolStripMenuItem.Name = "влевоToolStripMenuItem";
            this.влевоToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+←";
            this.влевоToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.Left)));
            this.влевоToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.влевоToolStripMenuItem.Text = "Влево";
            this.влевоToolStripMenuItem.Click += new System.EventHandler(this.влевоToolStripMenuItem_Click);
            //
            // вправоToolStripMenuItem
            //
            this.вправоToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("вправоToolStripMenuItem.Image")));
            this.вправоToolStripMenuItem.Name = "вправоToolStripMenuItem";
            this.вправоToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+→";
            this.вправоToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.Right)));
            this.вправоToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.вправоToolStripMenuItem.Text = "Вправо";
            this.вправоToolStripMenuItem.Click += new System.EventHandler(this.вправоToolStripMenuItem_Click);
            //
            // вверхToolStripMenuItem
            //
            this.вверхToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("вверхToolStripMenuItem.Image")));
            this.вверхToolStripMenuItem.Name = "вверхToolStripMenuItem";
            this.вверхToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+↑";
            this.вверхToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.Up)));
            this.вверхToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.вверхToolStripMenuItem.Text = "Вверх";
            this.вверхToolStripMenuItem.Click += new System.EventHandler(this.вверхToolStripMenuItem_Click);
            //
            // внизToolStripMenuItem
            //
            this.внизToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("внизToolStripMenuItem.Image")));
            this.внизToolStripMenuItem.Name = "внизToolStripMenuItem";
            this.внизToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+↓";
            this.внизToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.Down)));
            this.внизToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.внизToolStripMenuItem.Text = "Вниз";
            this.внизToolStripMenuItem.Click += new System.EventHandler(this.внизToolStripMenuItem_Click);
            //
            // видToolStripMenuItem
            //
            this.видToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.персонаж1ToolStripMenuItem,
            this.персонаж2ToolStripMenuItem,
            this.персонаж3ToolStripMenuItem});
            this.видToolStripMenuItem.Name = "видToolStripMenuItem";
            this.видToolStripMenuItem.Size = new System.Drawing.Size(39, 20);
            this.видToolStripMenuItem.Text = "&Вид";
            //
            // персонаж1ToolStripMenuItem
            //
            this.персонаж1ToolStripMenuItem.Name = "персонаж1ToolStripMenuItem";
            this.персонаж1ToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+1";
            this.персонаж1ToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.D1)));
            this.персонаж1ToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.персонаж1ToolStripMenuItem.Text = "Лосяш";
            this.персонаж1ToolStripMenuItem.Click += new System.EventHandler(this.персонаж1ToolStripMenuItem_Click);
            //
            // персонаж2ToolStripMenuItem
            //
            this.персонаж2ToolStripMenuItem.Name = "персонаж2ToolStripMenuItem";
            this.персонаж2ToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+2";
            this.персонаж2ToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.D2)));
            this.персонаж2ToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.персонаж2ToolStripMenuItem.Text = "Пин";
            this.персонаж2ToolStripMenuItem.Click += new System.EventHandler(this.персонаж2ToolStripMenuItem_Click);
            //
            // персонаж3ToolStripMenuItem
            //
            this.персонаж3ToolStripMenuItem.Name = "персонаж3ToolStripMenuItem";
            this.персонаж3ToolStripMenuItem.ShortcutKeyDisplayString = "Ctrl+3";
            this.персонаж3ToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.D3)));
            this.персонаж3ToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.персонаж3ToolStripMenuItem.Text = "Крош";
            this.персонаж3ToolStripMenuItem.Click += new System.EventHandler(this.персонаж3ToolStripMenuItem_Click);
            //
            // размерToolStripMenuItem
            //
            this.размерToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.большойToolStripMenuItem,
            this.маленькийToolStripMenuItem});
            this.размерToolStripMenuItem.Name = "размерToolStripMenuItem";
            this.размерToolStripMenuItem.Size = new System.Drawing.Size(59, 20);
            this.размерToolStripMenuItem.Text = "&Размер";
            //
            // большойToolStripMenuItem
            //
            this.большойToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("большойToolStripMenuItem.Image")));
            this.большойToolStripMenuItem.Name = "большойToolStripMenuItem";
            this.большойToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.B)));
            this.большойToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.большойToolStripMenuItem.Text = "Большой";
            this.большойToolStripMenuItem.Click += new System.EventHandler(this.большойToolStripMenuItem_Click);
            //
            // маленькийToolStripMenuItem
            //
            this.маленькийToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("маленькийToolStripMenuItem.Image")));
            this.маленькийToolStripMenuItem.Name = "маленькийToolStripMenuItem";
            this.маленькийToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.M)));
            this.маленькийToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.маленькийToolStripMenuItem.Text = "Маленький";
            this.маленькийToolStripMenuItem.Click += new System.EventHandler(this.маленькийToolStripMenuItem_Click);
            //
            // скоростьToolStripMenuItem
            //
            this.скоростьToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.медленноToolStripMenuItem,
            this.быстроToolStripMenuItem});
            this.скоростьToolStripMenuItem.Name = "скоростьToolStripMenuItem";
            this.скоростьToolStripMenuItem.Size = new System.Drawing.Size(71, 20);
            this.скоростьToolStripMenuItem.Text = "&Скорость";
            //
            // медленноToolStripMenuItem
            //
            this.медленноToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("медленноToolStripMenuItem.Image")));
            this.медленноToolStripMenuItem.Name = "медленноToolStripMenuItem";
            this.медленноToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.S)));
            this.медленноToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.медленноToolStripMenuItem.Text = "Медленно";
            this.медленноToolStripMenuItem.Click += new System.EventHandler(this.медленноToolStripMenuItem_Click);
            //
            // быстроToolStripMenuItem
            //
            this.быстроToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("быстроToolStripMenuItem.Image")));
            this.быстроToolStripMenuItem.Name = "быстроToolStripMenuItem";
            this.быстроToolStripMenuItem.ShortcutKeys = ((System.Windows.Forms.Keys)((System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.F)));
            this.быстроToolStripMenuItem.Size = new System.Drawing.Size(180, 22);
            this.быстроToolStripMenuItem.Text = "Быстро";
            this.быстроToolStripMenuItem.Click += new System.EventHandler(this.быстроToolStripMenuItem_Click);
            //
            // выходToolStripMenuItem
            //
            this.выходToolStripMenuItem.Image = ((System.Drawing.Image)(resources.GetObject("выходToolStripMenuItem.Image")));
            this.выходToolStripMenuItem.Name = "выходToolStripMenuItem";
            this.выходToolStripMenuItem.Size = new System.Drawing.Size(69, 20);
            this.выходToolStripMenuItem.Text = "Вы&ход";
            this.выходToolStripMenuItem.Click += new System.EventHandler(this.выходToolStripMenuItem_Click);
            //
            // toolStrip1
            //
            this.toolStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.toolStripButton1,
            this.toolStripButton2,
            this.toolStripButton3,
            this.toolStripButton4,
            this.toolStripSeparator1,
            this.toolStripComboBox1});
            this.toolStrip1.Location = new System.Drawing.Point(0, 24);
            this.toolStrip1.Name = "toolStrip1";
            this.toolStrip1.Size = new System.Drawing.Size(800, 25);
            this.toolStrip1.TabIndex = 2;
            this.toolStrip1.Text = "toolStrip1";
            //
            // toolStripButton1
            //
            this.toolStripButton1.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Image;
            this.toolStripButton1.Image = ((System.Drawing.Image)(resources.GetObject("toolStripButton1.Image")));
            this.toolStripButton1.ImageTransparentColor = System.Drawing.Color.Magenta;
            this.toolStripButton1.Name = "toolStripButton1";
            this.toolStripButton1.Size = new System.Drawing.Size(23, 22);
            this.toolStripButton1.Text = "Влево";
            this.toolStripButton1.Click += new System.EventHandler(this.toolStripButton1_Click);
            //
            // toolStripButton2
            //
            this.toolStripButton2.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Image;
            this.toolStripButton2.Image = ((System.Drawing.Image)(resources.GetObject("toolStripButton2.Image")));
            this.toolStripButton2.ImageTransparentColor = System.Drawing.Color.Magenta;
            this.toolStripButton2.Name = "toolStripButton2";
            this.toolStripButton2.Size = new System.Drawing.Size(23, 22);
            this.toolStripButton2.Text = "Вправо";
            this.toolStripButton2.Click += new System.EventHandler(this.toolStripButton2_Click);
            //
            // toolStripButton3
            //
            this.toolStripButton3.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Image;
            this.toolStripButton3.Image = ((System.Drawing.Image)(resources.GetObject("toolStripButton3.Image")));
            this.toolStripButton3.ImageTransparentColor = System.Drawing.Color.Magenta;
            this.toolStripButton3.Name = "toolStripButton3";
            this.toolStripButton3.Size = new System.Drawing.Size(23, 22);
            this.toolStripButton3.Text = "Вверх";
            this.toolStripButton3.Click += new System.EventHandler(this.toolStripButton3_Click);
            //
            // toolStripButton4
            //
            this.toolStripButton4.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Image;
            this.toolStripButton4.Image = ((System.Drawing.Image)(resources.GetObject("toolStripButton4.Image")));
            this.toolStripButton4.ImageTransparentColor = System.Drawing.Color.Magenta;
            this.toolStripButton4.Name = "toolStripButton4";
            this.toolStripButton4.Size = new System.Drawing.Size(23, 22);
            this.toolStripButton4.Text = "Вниз";
            this.toolStripButton4.Click += new System.EventHandler(this.toolStripButton4_Click);
            //
            // toolStripSeparator1
            //
            this.toolStripSeparator1.Name = "toolStripSeparator1";
            this.toolStripSeparator1.Size = new System.Drawing.Size(6, 25);
            //
            // toolStripComboBox1
            //
            this.toolStripComboBox1.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.toolStripComboBox1.Items.AddRange(new object[] {
            "Медленно",
            "Быстро"});
            this.toolStripComboBox1.Name = "toolStripComboBox1";
            this.toolStripComboBox1.Size = new System.Drawing.Size(121, 25);
            this.toolStripComboBox1.ToolTipText = "Скорость";
            this.toolStripComboBox1.SelectedIndexChanged += new System.EventHandler(this.toolStripComboBox1_SelectedIndexChanged);
            //
            // imageList1
            //
            this.imageList1.ImageStream = ((System.Windows.Forms.ImageListStreamer)(resources.GetObject("imageList1.ImageStream")));
            this.imageList1.TransparentColor = System.Drawing.Color.Transparent;
            this.imageList1.Images.SetKeyName(0, "fmt_114_24_1581696577_sm_cgi_losyash_012_02-copy.jpg");
            this.imageList1.Images.SetKeyName(1, "Пин.jpg");
            this.imageList1.Images.SetKeyName(2, "M_height.png");
            //
            // panel1
            //
            this.panel1.BackColor = System.Drawing.Color.White;
            this.panel1.Controls.Add(this.pictureBox1);
            this.panel1.Dock = System.Windows.Forms.DockStyle.Fill;
            this.panel1.Location = new System.Drawing.Point(0, 49);
            this.panel1.Name = "panel1";
            this.panel1.Size = new System.Drawing.Size(800, 401);
            this.panel1.TabIndex = 3;
            //
            // Form1
            //
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(800, 450);
            this.Controls.Add(this.panel1);
            this.Controls.Add(this.toolStrip1);
            this.Controls.Add(this.menuStrip1);
            this.MainMenuStrip = this.menuStrip1;
            this.MinimumSize = new System.Drawing.Size(400, 300);
            this.Name = "Form1";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Практика 6: управление объектом";
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).EndInit();
            this.contextMenuStrip1.ResumeLayout(false);
            this.menuStrip1.ResumeLayout(false);
            this.menuStrip1.PerformLayout();
            this.toolStrip1.ResumeLayout(false);
            this.toolStrip1.PerformLayout();
            this.panel1.ResumeLayout(false);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.PictureBox pictureBox1;
        private System.Windows.Forms.Timer timer1;
        private System.Windows.Forms.MenuStrip menuStrip1;
        private System.Windows.Forms.ToolStripMenuItem направлениеToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem влевоToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem вправоToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem вверхToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem внизToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem видToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem персонаж1ToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem персонаж2ToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem персонаж3ToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem размерToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem большойToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem маленькийToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem скоростьToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem медленноToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem быстроToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem выходToolStripMenuItem;
        private System.Windows.Forms.ToolStrip toolStrip1;
        private System.Windows.Forms.ToolStripButton toolStripButton1;
        private System.Windows.Forms.ToolStripButton toolStripButton2;
        private System.Windows.Forms.ToolStripButton toolStripButton3;
        private System.Windows.Forms.ToolStripButton toolStripButton4;
        private System.Windows.Forms.ToolStripSeparator toolStripSeparator1;
        private System.Windows.Forms.ToolStripComboBox toolStripComboBox1;
        private System.Windows.Forms.ImageList imageList1;
        private System.Windows.Forms.Panel panel1;
        private System.Windows.Forms.ContextMenuStrip contextMenuStrip1;
        private System.Windows.Forms.ToolStripMenuItem контекстПерсонаж1ToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem контекстПерсонаж2ToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem контекстПерсонаж3ToolStripMenuItem;
    }
}
